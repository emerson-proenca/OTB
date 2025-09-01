# jobs/sync_tournaments.py
import logging
from scrapers.cbx.cbx_tournaments import fetch_tournaments_raw
from database.session import SessionLocal
from database.models import Tournament, SyncJob
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import requests


logger = logging.getLogger("sync_tournaments")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

def upsert_tournament(db, item):
    q = db.query(Tournament).filter(
        Tournament.federation == item.get("federation"),
        Tournament.external_id == item.get("external_id")
    ).one_or_none()

    if q:
        q.name = item.get("name") or q.name
        q.status = item.get("status")
        q.time_control = item.get("time_control")
        q.rating = item.get("rating")
        try:
            q.total_players = int(item.get("total_players")) if item.get("total_players") else None
        except Exception:
            q.total_players = None
        q.organizer = item.get("organizer")
        q.place = item.get("place")
        try:
            q.fide_players = int(item.get("fide_players")) if item.get("fide_players") else None
        except Exception:
            q.fide_players = None
        q.period = item.get("period")
        q.observation = item.get("observation")
        q.regulation = item.get("regulation")
        q.year = item.get("year")
        q.month = item.get("month")
        q.scraped_at = datetime.now(timezone.utc)
        return q
    else:
        t = Tournament(
            federation=item.get("federation"),
            external_id=item.get("external_id"),
            name=item.get("name") or "unnamed",
            status=item.get("status"),
            time_control=item.get("time_control"),
            rating=item.get("rating"),
            total_players=int(item.get("total_players")) if item.get("total_players") else None,
            organizer=item.get("organizer"),
            place=item.get("place"),
            fide_players=int(item.get("fide_players")) if item.get("fide_players") else None,
            period=item.get("period"),
            observation=item.get("observation"),
            regulation=item.get("regulation"),
            year=item.get("year"),
            month=item.get("month"),
        )
        db.add(t)
        return t

def sync_cbxtournaments(year=None, month=None, limit=None):
    # 1) criar registro de job
    job_db = SessionLocal()
    job = SyncJob(federation="cbx", status="started")
    job_db.add(job)
    job_db.commit()
    job_db.refresh(job)
    job_id = job.id
    job_db.close()

    created = 0
    updated = 0

    try:
        rows = fetch_tournaments_raw(year, month, limit)
    except requests.exceptions.RequestException as e:
        # atualizar job como failed e salvar erro
        dbj = SessionLocal()
        j = dbj.get(SyncJob, job_id)
        if j:
            j.finished_at = datetime.now(timezone.utc)
            j.status = "failed"
            j.error = f"UnexpectedError: {str(e)}"
            dbj.commit()
        dbj.close()
        logger.exception("Erro de rede ao buscar dados da CBX. Sync abortado.")
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
        logger.exception("Erro inesperado ao buscar dados da CBX. Sync abortado.")
        return

    # 2) processar linhas e persistir (commits periódicos)
    db = SessionLocal()
    try:
        for r in rows:
            try:
                existing = db.query(Tournament).filter(
                    Tournament.federation == r.get("federation"),
                    Tournament.external_id == r.get("external_id")
                ).one_or_none()
                if existing:
                    upsert_tournament(db, r)
                    updated += 1
                else:
                    upsert_tournament(db, r)
                    created += 1
                db.commit()
            except IntegrityError:
                db.rollback()
                logger.exception("IntegrityError ao inserir/atualizar um torneio, pulando.")
            except Exception:
                db.rollback()
                logger.exception("Erro ao processar um torneio individual, pulando.")
        logger.info(f"Sync complete: created={created}, updated={updated}")
    except Exception:
        db.rollback()
        logger.exception("Erro durante loop de sync")
    finally:
        db.close()

    # 3) atualizar registro de job como sucesso
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
    parser.add_argument("--year", default=None)
    parser.add_argument("--month", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    sync_cbxtournaments(year=args.year, month=args.month, limit=args.limit)