# apis/news_api.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from database.session import SessionLocal
from database.models import CBXNews
import logging

router = APIRouter(prefix="/news", tags=["news"])
logger = logging.getLogger("apis.news")

def _safe_str(v) -> str:
    if v is None:
        return ""
    return str(v)

@router.get("", response_model=List[dict])
def get_news(limit: int = Query(50, ge=1, le=500), latest: bool = Query(True)):
    """
    Returns recent news from DB.
    """
    db = SessionLocal()
    try:
        q = db.query(CBXNews)
        if latest:
            q = q.order_by(CBXNews.scraped_at.desc())
        results = q.limit(limit).all()

        out = []
        for r in results:
            out.append({
                "title": _safe_str(r.title),
                "date_text": _safe_str(r.date_text),
                "link": _safe_str(r.link),
                "summary": _safe_str(r.summary)
            })
        return out
    except Exception:
        logger.exception("Error building news response")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()
