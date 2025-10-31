import logging
from typing import Optional, List, Dict, Any
from datetime import date

from fastapi import APIRouter, Query, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from core.schemas import CBXTournamentResponse, TournamentCreate, TournamentUpdate
from db.session import SessionLocal
from db.models import Tournament, Club
from core.utils import verify_club_jwt

# Logger
logger = logging.getLogger("apis.tournaments")

router = APIRouter(prefix="/tournaments", tags=["Tournaments"])

# =========================================
#              DEPENDENCY
# =========================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================================
#               GET ALL
# =========================================
@router.get("", response_model=CBXTournamentResponse)
def get_tournaments(
    db: Session = Depends(get_db),
    federation: Optional[str] = Query(None),
    year: Optional[str] = Query(None, min_length=4, max_length=4),
    month: Optional[str] = Query(None, max_length=2),
    limit: int = Query(32, ge=1),
):
    """Retorna uma lista de torneios, com filtros opcionais."""
    try:
        q = db.query(Tournament)
        if federation:
            q = q.filter(Tournament.federation == federation.lower())
        if year:
            q = q.filter(Tournament.year == year)
        if month:
            q = q.filter(Tournament.month == month)

        tournaments = q.order_by(Tournament.scraped_at.desc()).limit(limit).all()

        cbx = []
        for t in tournaments:
            cbx.append({
                "page": getattr(t, "page", 1),
                "name": t.title or "",
                "id": t.external_id or "",
                "status": t.status or "",
                "time_control": t.time_control or "",
                "rating": t.rating or "",
                "total_players": t.total_players or "",
                "organizer": t.organizer or "",
                "place": t.place or "",
                "fide_players": t.fide_players or "",
                "period": t.period or "",
                "observation": t.observation or "",
                "regulation": t.regulation or "",
            })

        return CBXTournamentResponse(cbx=cbx)

    except Exception as e:
        logger.exception("Erro ao buscar torneios")
        raise HTTPException(status_code=500, detail="Erro ao listar torneios")

# =========================================
#              GET ONE
# =========================================
@router.get("/{title}")
def get_tournament(title: str, db: Session = Depends(get_db)):
    """Retorna um único torneio pelo título."""
    tournament = db.query(Tournament).filter(Tournament.title == title).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament

# =========================================
#               CREATE
# =========================================
@router.post("", status_code=201)
async def create_tournament(
    tournament_data: TournamentCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Cria um novo torneio (somente clubes)."""
    club = verify_club_jwt(request, db)
    if not club:
        raise HTTPException(status_code=403, detail="Only clubs can create tournaments")

    tournament = Tournament(
        **tournament_data.model_dump(exclude_unset=True),
        club_id=club.id
    )

    try:
        db.add(tournament)
        db.commit()
        db.refresh(tournament)
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception("Erro ao criar torneio")
        raise HTTPException(status_code=500, detail="Erro ao criar torneio")

    return {"message": "Tournament created successfully", "tournament": tournament}

# =========================================
#               UPDATE
# =========================================
@router.put("/{title}")
async def update_tournament(
    title: str,
    data: TournamentUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Atualiza um torneio (somente o dono do clube)."""
    club = verify_club_jwt(request, db)
    if not club:
        raise HTTPException(status_code=403, detail="Only clubs can update tournaments")

    tournament = db.query(Tournament).filter(Tournament.title == title).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament.club_id != club.id:
        raise HTTPException(status_code=403, detail="You do not own this tournament")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tournament, field, value)

    db.commit()
    db.refresh(tournament)
    return {"message": "Tournament updated successfully", "tournament": tournament}

# =========================================
#               DELETE
# =========================================
@router.delete("/{title}")
async def delete_tournament(
    title: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Remove um torneio (somente o dono do clube)."""
    club = verify_club_jwt(request, db)
    if not club:
        raise HTTPException(status_code=403, detail="Only clubs can delete tournaments")

    tournament = db.query(Tournament).filter(Tournament.title == title).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    if tournament.club_id != club.id:
        raise HTTPException(status_code=403, detail="You do not own this tournament")

    db.delete(tournament)
    db.commit()
    return {"message": "Tournament deleted successfully"}
