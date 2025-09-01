# jobs/sync_players.py
import logging
from datetime import datetime, timezone
from typing import Optional
from database.session import SessionLocal
from database.models import CBXPlayer, SyncJob
from scrapers.cbx.cbx_players import fetch_players_raw
import requests

logger = logging.getLogger("sync_players")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

def upsert_player(db, item: dict):
    local_id = item.get("local_id") or ""
    if not local_id:
        return None  # skip invalid
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
        return q
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
        )
        db.add(p)
        return p

def sync_cbxplayers(state: str = "SP", max_pages: Optional[int] = None, limit: Optional[int] = None):
    """
    Faz sync dos jogadores do estado especificado.
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
            j.error = f"NetworkError: {str(e)}"
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
                existing = db.query(CBXPlayer).filter(CBXPlayer.local_id == p.get("local_id")).one_or_none()
                if existing:
                    upsert_player(db, p)
                    updated += 1
                else:
                    upsert_player(db, p)
                    created += 1
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
    parser.add_argument("--state", default="SP")
    parser.add_argument("--pages", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    sync_cbxplayers(state=args.state, max_pages=args.pages, limit=args.limit)
