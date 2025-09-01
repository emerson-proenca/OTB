# jobs/sync_news.py
import logging
from datetime import datetime, timezone
from typing import Optional
from database.session import SessionLocal
from database.models import CBXNews, SyncJob
from scrapers.cbx.cbx_news import fetch_news_raw
import requests

logger = logging.getLogger("sync_news")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

def upsert_news(db, item: dict):
    link = item.get("link") or ""
    if not link:
        return None
    q = db.query(CBXNews).filter(CBXNews.link == link).one_or_none()
    if q:
        q.title = item.get("title") or q.title
        q.date_text = item.get("date_text")
        q.summary = item.get("summary")
        q.scraped_at = datetime.now(timezone.utc)
        return q
    else:
        n = CBXNews(
            title=item.get("title") or "untitled",
            date_text=item.get("date_text"),
            link=link,
            summary=item.get("summary"),
        )
        db.add(n)
        return n

def sync_cbxnews(max_pages: Optional[int] = None, limit: Optional[int] = None):
    db_job = SessionLocal()
    job = SyncJob(federation="cbx_news", status="started")
    db_job.add(job)
    db_job.commit()
    db_job.refresh(job)
    job_id = job.id
    db_job.close()

    created = 0
    updated = 0

    try:
        news_items = fetch_news_raw(max_pages=max_pages)
    except requests.exceptions.RequestException as e:
        dbj = SessionLocal()
        j = dbj.query(SyncJob).get(job_id)
        j.finished_at = datetime.now(timezone.utc)
        j.status = "failed"
        j.error = f"NetworkError: {str(e)}"
        dbj.commit()
        dbj.close()
        logger.exception("Network error fetching CBX news. Sync aborted.")
        return
    except Exception as e:
        dbj = SessionLocal()
        j = dbj.query(SyncJob).get(job_id)
        j.finished_at = datetime.now(timezone.utc)
        j.status = "failed"
        j.error = f"UnexpectedError: {str(e)}"
        dbj.commit()
        dbj.close()
        logger.exception("Unexpected error fetching CBX news. Sync aborted.")
        return

    db = SessionLocal()
    try:
        for i, item in enumerate(news_items):
            if limit and i >= limit:
                break
            try:
                existing = db.query(CBXNews).filter(CBXNews.link == item.get("link")).one_or_none()
                if existing:
                    upsert_news(db, item)
                    updated += 1
                else:
                    upsert_news(db, item)
                    created += 1
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Error processing individual news item, skipping.")
        logger.info(f"Sync news complete: created={created}, updated={updated}")
    except Exception:
        db.rollback()
        logger.exception("Error during news sync loop")
    finally:
        db.close()

    db_job2 = SessionLocal()
    j = db_job2.query(SyncJob).get(job_id)
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
    sync_cbxnews(max_pages=args.max_pages, limit=args.limit)
