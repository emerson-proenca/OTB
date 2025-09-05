# jobs/sync_players.py
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple
from database.session import SessionLocal
from database.models import CBXPlayer, SyncJob
from scrapers.cbx.cbx_players import fetch_players_raw
import requests

logger = logging.getLogger("sync_players")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# Lista de UFs do Brasil para full import quando se usa --state ALL
BRAZIL_STATES = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
    "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"
]


def upsert_player(db, item: dict) -> Tuple[Optional[CBXPlayer], bool]:
    """
    Upsert a single player record. Returns (instance, created_bool)
    """
    local_id = item.get("local_id") or ""
    if not local_id:
        return None, False  # skip invalid

    q = db.query(CBXPlayer).filter(CBXPlayer.local_id == local_id).one_or_none()
    if q:
        # update fields
        q.name = item.get("name") or q.name
        q.birthday = item.get("birthday")
        q.gender = item.get("gender")
        q.country = item.get("country")
        q.state = item.get("state")
        q.classical = item.get("classical")
        q.rapid = item.get("rapid")
        q.blitz = item.get("blitz")
        q.fide_id = item.get("fide_id")
        q.local_profile = item.get("local_profile")
        q.scraped_at = datetime.now(timezone.utc)
        return q, False
    else:
        p = CBXPlayer(
            local_id=local_id,
            name=item.get("name") or "unknown",
            birthday=item.get("birthday"),
            gender=item.get("gender"),
            country=item.get("country"),
            state=item.get("state"),
            classical=item.get("classical"),
            rapid=item.get("rapid"),
            blitz=item.get("blitz"),
            fide_id=item.get("fide_id"),
            local_profile=item.get("local_profile"),
            scraped_at=datetime.now(timezone.utc)
        )
        db.add(p)
        return p, True


def _run_fetch_and_persist_for_state(state: str, max_pages: Optional[int], limit: Optional[int], created_updated: Dict[str, int]) -> None:
    """
    Fetch players for a single state and persist them, updating created_updated dict in-place.
    This function catches fetch errors and logs them, but does NOT raise to allow full-import to continue.
    """
    try:
        players = fetch_players_raw(state=state, max_pages=max_pages)
    except requests.exceptions.RequestException as e:
        logger.exception(f"Network error fetching players for state {state}: {e}. Skipping this state.")
        return
    except Exception as e:
        logger.exception(f"Unexpected error fetching players for state {state}: {e}. Skipping this state.")
        return

    if not players:
        logger.info(f"No players returned for state {state}.")
        return

    db = SessionLocal()
    try:
        for i, p in enumerate(players):
            if limit is not None and i >= limit:
                break
            try:
                instance, created_flag = upsert_player(db, p)
                if instance is None:
                    continue
                if created_flag:
                    created_updated["created"] += 1
                else:
                    created_updated["updated"] += 1
                db.commit()
            except Exception:
                db.rollback()
                logger.exception(f"Error persisting player {p.get('local_id')} for state {state}, skipping.")
    finally:
        db.close()


def sync_cbxplayers(state: str = "SP", max_pages: Optional[int] = None, limit: Optional[int] = None, full: bool = False):
    """
    Faz sync dos jogadores do estado especificado.

    If full=True:
      - cleans CBXPlayer table (federation-wide) and repopulates.
      - if state == 'ALL' -> run through all BRAZIL_STATES
      - accumulates created/updated counts across states
    """
    # create SyncJob entry
    db_job = SessionLocal()
    job = SyncJob(federation="cbx_players", status="started")
    db_job.add(job)
    db_job.commit()
    db_job.refresh(job)
    job_id = job.id
    db_job.close()

    created = 0
    updated = 0

    # FULL mode
    if full:
        logger.info("FULL mode enabled for CBX players: cleaning CBXPlayer table before full import.")
        db_clean = SessionLocal()
        try:
            deleted = db_clean.query(CBXPlayer).delete(synchronize_session=False)
            db_clean.commit()
            logger.info(f"Deleted {deleted} existing CBX players (cleanup before full import).")
        except Exception:
            db_clean.rollback()
            logger.exception("Failed cleaning CBX players before full import.")
        finally:
            db_clean.close()

        # Determine states to iterate
        states_to_run: List[str] = []
        if isinstance(state, str) and state.strip().lower() == "all":
            states_to_run = BRAZIL_STATES
        else:
            states_to_run = [state]

        # Run for each state; continue on errors
        totals = {"created": 0, "updated": 0}
        for st in states_to_run:
            logger.info(f"Full import players: fetching state={st}")
            try:
                _run_fetch_and_persist_for_state(st, max_pages=max_pages, limit=limit, created_updated=totals)
            except Exception:
                # Safety net: _run_fetch_and_persist_for_state should catch its own exceptions,
                # but in case something bubbles up, we log and continue.
                logger.exception(f"Unhandled exception while processing state {st}; continuing to next state.")
                continue

        created = totals["created"]
        updated = totals["updated"]

        # finalize job as success
        db_job2 = SessionLocal()
        j = db_job2.get(SyncJob, job_id)
        if j:
            j.finished_at = datetime.now(timezone.utc)
            j.status = "success"
            j.created = created
            j.updated = updated
            db_job2.commit()
        db_job2.close()
        logger.info(f"FULL players import finished: created={created}, updated={updated}")
        return

    # Non-FULL (incremental) mode: normal single-state fetch
    try:
        players = fetch_players_raw(state=state, max_pages=max_pages)
    except requests.exceptions.RequestException as e:
        dbj = SessionLocal()
        j = dbj.get(SyncJob, job_id)
        if j:
            j.finished_at = datetime.now(timezone.utc)
            j.status = "failed"
            j.error = f"NetworkError: {str(e)}"
            dbj.commit()
        dbj.close()
        logger.exception("Network error fetching CBX players. Sync aborted.")
        return
    except Exception as e:
        dbj = SessionLocal()
        j = dbj.get(SyncJob, job_id)
        if j:
            j.finished_at = datetime.now(timezone.utc)
            j.status = "failed"
            j.error = f"UnexpectedError: {str(e)}"
            dbj.commit()
        dbj.close()
        logger.exception("Unexpected error fetching CBX players. Sync aborted.")
        return

    db = SessionLocal()
    try:
        for i, p in enumerate(players):
            if limit and i >= limit:
                break
            try:
                instance, created_flag = upsert_player(db, p)
                if instance is None:
                    continue
                if created_flag:
                    created += 1
                else:
                    updated += 1
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Error processing individual player, skipping.")
        logger.info(f"Sync players complete: created={created}, updated={updated}")
    except Exception:
        db.rollback()
        logger.exception("Error during players sync loop")
    finally:
        db.close()

    # finalize job record
    db_job2 = SessionLocal()
    j = db_job2.get(SyncJob, job_id)
    if j:
        j.finished_at = datetime.now(timezone.utc)
        j.status = "success"
        j.created = created
        j.updated = updated
        db_job2.commit()
    db_job2.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default="all")
    parser.add_argument("--pages", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--full", action="store_true", help="Run full import for players. Use --state ALL to import all UFs.")
    args = parser.parse_args()
    sync_cbxplayers(state=args.state, max_pages=args.pages, limit=args.limit, full=args.full)
