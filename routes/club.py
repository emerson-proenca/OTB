from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from db.session import get_db
from db.models import Club, Tournament
from starlette.templating import Jinja2Templates
from urllib.parse import unquote_plus, quote_plus

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/club", tags=["Club Pages"])

@router.get("/{club_name}", response_class=HTMLResponse)
async def club_page(request: Request, club_name: str, db: Session = Depends(get_db)):
    """Renderiza a página de um clube e seus torneios"""
    decoded_name = unquote_plus(club_name)
    club = db.query(Club).filter(Club.name == decoded_name).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    tournaments = (
        db.query(Tournament)
        .filter(Tournament.club_id == club.id)
        .order_by(Tournament.start_date.desc())
        .all()
    )

    # Codifica nomes dos torneios para gerar links válidos
    for t in tournaments:
        t.encoded_title = quote_plus(str(t.title))

    context = {
        "request": request,
        "club": club,
        "tournaments": tournaments,
        "current_user": getattr(request.state, "current_user", None),
    }

    return templates.TemplateResponse("club.html", context)


@router.get("/{club_name}/tournament/{tournament_title}", response_class=HTMLResponse)
async def tournament_page(
    request: Request, club_name: str, tournament_title: str, db: Session = Depends(get_db)
):
    """Renderiza a página de um torneio pertencente a um clube"""
    decoded_club_name = unquote_plus(club_name)
    decoded_title = unquote_plus(tournament_title)

    club = db.query(Club).filter(Club.name == decoded_club_name).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    tournament = (
        db.query(Tournament)
        .filter(Tournament.title == decoded_title, Tournament.club_id == club.id)
        .first()
    )
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found for this club")

    context = {
        "request": request,
        "club": club,
        "tournament": tournament,
        "current_user": getattr(request.state, "current_user", None),
    }

    return templates.TemplateResponse("tournament.html", context)
