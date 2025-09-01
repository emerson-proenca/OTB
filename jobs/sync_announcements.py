# jobs/sync_announcements.py
import logging
from datetime import datetime, timezone
from typing import Optional
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
        q.scraped_at = datetime.now(timezone.utc)
        return q
    else:
        a = CBXAnnouncement(
            title=item.get("title") or "untitled",
            date_text=item.get("date_text"),
            link=link,
            content=item.get("content")
        )
        db.add(a)
        return a

def sync_cbxannouncements(max_pages: Optional[int] = None, limit: Optional[int] = None):
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

    try:
        announcements = fetch_announcements_raw(max_pages=max_pages)
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
            j.error = f"NetworkError: {str(e)}"
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
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    sync_cbxannouncements(max_pages=args.max_pages, limit=args.limit)