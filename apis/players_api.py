# apis/players_api.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from database.session import SessionLocal
from database.models import CBXPlayer
from core.schemas import CBXPlayerResponse
import logging

router = APIRouter(prefix="/players", tags=["players"])
logger = logging.getLogger("apis.players")

def _safe_str(v) -> str:
    if v is None:
        return ""
    return str(v)

@router.get("", response_model=CBXPlayerResponse)
def get_players(
    state: Optional[str] = Query(None, min_length=2, max_length=2, description="State (e.g. SP)"),
    limit: int = Query(50, ge=1, le=500)
):
    db = SessionLocal()
    try:
        q = db.query(CBXPlayer)
        if state:
            q = q.filter(CBXPlayer.state == state)
        q = q.order_by(CBXPlayer.scraped_at.desc())
        results = q.limit(limit).all()

        players = []
        for p in results:
            players.append({
                "local_id": _safe_str(p.local_id),
                "name": _safe_str(p.name),
                "birthday": _safe_str(p.birthday),
                "gender": _safe_str(p.gender),
                "country": _safe_str(p.country),
                "state": _safe_str(p.state),
                "classical": _safe_str(p.classical),
                "rapid": _safe_str(p.rapid),
                "blitz": _safe_str(p.blitz),
                "fide_id": _safe_str(p.fide_id),
                "local_profile": _safe_str(p.local_profile)
            })

        return CBXPlayerResponse(cbx=players)
    except Exception:
        logger.exception("Error building players response")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        db.close()
