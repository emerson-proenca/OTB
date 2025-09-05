# jobs/sync_news.py
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, List
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
            scraped_at=datetime.now(timezone.utc)
        )
        db.add(n)
        return n


def sync_cbxnews(max_pages: Optional[int] = None, limit: Optional[int] = None, full: bool = False):
    db_job = SessionLocal()
    job = SyncJob(federation="cbx_news", status="started")
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
        logger.info("FULL mode enabled for CBX news: cleaning CBXNews table before full import.")
        db_clean = SessionLocal()
        try:
            deleted = db_clean.query(CBXNews).delete(synchronize_session=False)
            db_clean.commit()
            logger.info(f"Deleted {deleted} existing CBX news (cleanup before full import).")
        except Exception:
            db_clean.rollback()
            logger.exception("Failed cleaning CBX news before full import.")
        finally:
            db_clean.close()

    try:
        # fetch_news_raw now returns (items, failed_pages)
        news_items, failed_pages = fetch_news_raw(max_pages=max_pages)
    except requests.exceptions.RequestException as e:
        dbj = SessionLocal()
        j = dbj.get(SyncJob, job_id)
        if j:
            j.finished_at = datetime.now(timezone.utc)
            j.status = "failed"
            j.error = f"NetworkError: {str(e)}"
            dbj.commit()
        dbj.close()
        logger.exception("Network error fetching CBX news. Sync aborted.")
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

    # finalize job record and log failed pages if any
    db_job2 = SessionLocal()
    j = db_job2.get(SyncJob, job_id)
    if j:
        j.finished_at = datetime.now(timezone.utc)
        j.status = "success"
        j.created = created
        j.updated = updated
        if failed_pages:
            # save a short summary in the job error field for later inspection
            j.error = f"Failed pages: {len(failed_pages)}"
        db_job2.commit()
    db_job2.close()

    if failed_pages:
        logger.warning("Some pages failed during news scraping. Failed pages / identifiers:")
        for fp in failed_pages:
            logger.warning(f" - {fp}")
    else:
        logger.info("No failed pages during news scraping.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--full", action="store_true", help="Run full import (cleans CBXNews then imports all pages).")
    args = parser.parse_args()
    sync_cbxnews(max_pages=args.max_pages, limit=args.limit, full=args.full)
