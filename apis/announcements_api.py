# apis/announcements_api.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from database.session import SessionLocal
from database.models import CBXAnnouncement
import logging

router = APIRouter(prefix="/announcements", tags=["announcements"])
logger = logging.getLogger("apis.announcements")

def _safe_str(v) -> str:
    if v is None:
        return ""
    return str(v)

@router.get("", response_model=List[dict])
def get_announcements(limit: int = Query(50, ge=1, le=500), latest: bool = Query(True)):
    """
    Returns list of announcements from DB.
    - limit: max items returned
    - latest: if True, orders by scraped_at desc
    """
    db = SessionLocal()
    try:
        q = db.query(CBXAnnouncement)
        if latest:
            q = q.order_by(CBXAnnouncement.scraped_at.desc())
        results = q.limit(limit).all()

        out = []
        for r in results:
            out.append({
                "title": _safe_str(r.title),
                "date_text": _safe_str(r.date_text),
                "link": _safe_str(r.link),
                "content": _safe_str(r.content),
                "scraped_at": r.scraped_at.isoformat() if getattr(r, "scraped_at", None) else None
            })
        return out
    except Exception:
        logger.exception("Error building announcements response")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()
