# jobs/sync_announcements.py
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from database.session import SessionLocal
from database.models import CBXAnnouncement, SyncJob
from scrapers.cbx.cbx_announcements import fetch_announcements_raw
import requests

logger = logging.getLogger("sync_announcements")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def upsert_announcement(db, item: dict):
    link = item.get("link") or ""
    if not link:
        return None
    q = db.query(CBXAnnouncement).filter(CBXAnnouncement.link == link).one_or_none()
    if q:
        q.title = item.get("title") or q.title
        q.date_text = item.get("date_text")
        q.content = item.get("content")
        q.scraped_at = datetime.now(timezone.utc)
        return q
    else:
        a = CBXAnnouncement(
            title=item.get("title") or "untitled",
            date_text=item.get("date_text"),
            link=link,
            content=item.get("content"),
            scraped_at=datetime.now(timezone.utc)
        )
        db.add(a)
        return a


def sync_cbxannouncements(max_pages: Optional[int] = None, limit: Optional[int] = None, full: bool = False):
    # create SyncJob entry
    db_job = SessionLocal()
    job = SyncJob(federation="cbx_announcements", status="started")
    db_job.add(job)
    db_job.commit()
    db_job.refresh(job)
    job_id = job.id
    db_job.close()

    created = 0
    updated = 0
    failed_pages: List[str] = []

    # FULL mode: clean table first
    if full:
        logger.info("FULL mode enabled for CBX announcements: cleaning CBXAnnouncement table before full import.")
        db_clean = SessionLocal()
        try:
            deleted = db_clean.query(CBXAnnouncement).delete(synchronize_session=False)
            db_clean.commit()
            logger.info(f"Deleted {deleted} existing CBX announcements (cleanup before full import).")
        except Exception:
            db_clean.rollback()
            logger.exception("Failed cleaning CBX announcements before full import.")
        finally:
            db_clean.close()

    try:
        announcements, failed_pages = fetch_announcements_raw(max_pages=max_pages)
    except requests.exceptions.RequestException as e:
        dbj = SessionLocal()
        j = dbj.get(SyncJob, job_id)
        if j:
            j.finished_at = datetime.now(timezone.utc)
            j.status = "failed"
            j.error = f"NetworkError: {str(e)}"
            dbj.commit()
        dbj.close()
        logger.exception("Network error fetching CBX announcements. Sync aborted.")
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
        logger.exception("Unexpected error fetching CBX announcements. Sync aborted.")
        return

    db = SessionLocal()
    try:
        for i, item in enumerate(announcements):
            if limit and i >= limit:
                break
            try:
                existing = db.query(CBXAnnouncement).filter(CBXAnnouncement.link == item.get("link")).one_or_none()
                if existing:
                    upsert_announcement(db, item)
                    updated += 1
                else:
                    upsert_announcement(db, item)
                    created += 1
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Error processing individual announcement, skipping.")
        logger.info(f"Sync announcements complete: created={created}, updated={updated}")
    except Exception:
        db.rollback()
        logger.exception("Error during announcements sync loop")
    finally:
        db.close()

    # finalize job record and log failed pages if any
    db_job2 = SessionLocal()
    j = db_job2.get(SyncJob, job_id)
    if j:
        j.finished_at = datetime.now(timezone.utc)
        j.status = "success"
        j.created = created
        j.updated = updated
        if failed_pages:
            j.error = f"Failed pages: {len(failed_pages)}"
        db_job2.commit()
    db_job2.close()

    if failed_pages:
        logger.warning("Some pages failed during announcements scraping. Failed pages / identifiers:")
        for fp in failed_pages:
            logger.warning(f" - {fp}")
    else:
        logger.info("No failed pages during announcements scraping.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--full", action="store_true", help="Run full import (cleans CBXAnnouncement then imports all pages).")
    args = parser.parse_args()
    sync_cbxannouncements(max_pages=args.max_pages, limit=args.limit, full=args.full)
