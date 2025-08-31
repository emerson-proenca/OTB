# apis/status_api.py
from fastapi import APIRouter
from database.session import SessionLocal
from database.models import SyncJob
from typing import Optional

router = APIRouter(prefix="/status", tags=["status"])

@router.get("/sync")
def get_last_sync(federation: Optional[str] = "cbx"):
    db = SessionLocal()
    try:
        job = db.query(SyncJob).filter(SyncJob.federation == federation).order_by(SyncJob.started_at.desc()).first()
        if not job:
            return {"federation": federation, "last_sync": None, "status": None}
        return {
            "federation": federation,
            "last_sync": job.finished_at.isoformat() if job.finished_at else job.started_at.isoformat(),
            "status": job.status,
            "created": job.created,
            "updated": job.updated,
            "error": job.error
        }
    finally:
        db.close()
