import logging
from typing import Optional, List, Dict, Any
from datetime import date
# Não precisamos de json.decoder.JSONDecodeError porque estamos usando o Pydantic BaseModel

from fastapi import APIRouter, Query, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session

# ESSENCIAL: Todos os Schemas Pydantic devem vir daqui.
from core.schemas import CBXTournamentResponse, TournamentCreate 
from db.session import SessionLocal
from db.models import Tournament, Club
from core.utils import verify_club_jwt 

# Configuração do Logger
logger = logging.getLogger("apis.tournaments")

# Funções de Utilidade (melhor usar um util se forem grandes)
def _safe_str(v: Any) -> str:
    """Retorna uma string segura, evitando 'None' como string literal."""
    return str(v) if v is not None else ""

def _safe_int_for_page(v: Any) -> int:
    """Converte para int de forma segura, default 1."""
    try:
        return int(v) if v is not None and str(v).isdigit() else 1
    except (ValueError, TypeError):
        return 1

# Dependency para o Banco de Dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.get("", response_model=CBXTournamentResponse) # Usa o tipo importado corretamente
def get_tournaments(
    db: Session = Depends(get_db), 
    federation: Optional[str] = Query(None, description="Sigla da federação (cbx, fide, uscf…)."),
    year: Optional[str] = Query(None, min_length=4, max_length=4, description="Ano, ex: 2025"),
    month: Optional[str] = Query("", max_length=2, description="Mês (1–12) ou vazio"),
    limit: int = Query(32, ge=1, description="Máximo de torneios a retornar") 
):
    """Retorna uma lista de torneios, com filtros opcionais."""
    try:
        q = db.query(Tournament)
        
        # Filtros
        if federation:
            q = q.filter(Tournament.federation == federation.lower())
        if year:
            q = q.filter(Tournament.year == year)
        if month:
            q = q.filter(Tournament.month == month)
            
        # Ordenação e Limite
        q = q.order_by(Tournament.scraped_at.desc()) 
        results: List[Tournament] = q.limit(limit).all() 

        cbx = []
        for t in results:
            page_val = _safe_int_for_page(getattr(t, "page", 1)) 

            cbx_item: Dict[str, Any] = {
                "page": page_val,
                "name": _safe_str(t.title), 
                "id": _safe_str(t.external_id) or "",
                "status": _safe_str(t.status),
                "time_control": _safe_str(t.time_control),
                "rating": _safe_str(t.rating),
                "total_players": _safe_str(t.total_players), 
                "organizer": _safe_str(t.organizer),
                "place": _safe_str(t.place),
                "fide_players": _safe_str(t.fide_players), 
                "period": _safe_str(t.period),
                "observation": _safe_str(t.observation),
                "regulation": _safe_str(t.regulation),
            }
            cbx.append(cbx_item)

        return CBXTournamentResponse(cbx=cbx)
        
    except Exception as e:
        logger.exception("Erro ao construir resposta de torneios. Verifique o modelo/colunas.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Internal server error building tournament response"
        )


@router.post("/create", status_code=201)
async def create_tournament(
    tournament_data: TournamentCreate, 
    request: Request,
    db: Session = Depends(get_db)
):
    """Cria um novo torneio (somente clubes)"""
    
    # Verifica JWT de Clube
    club: Club = verify_club_jwt(request, db)
    if not club:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only clubs can create tournaments")

    # Cria o torneio.
    tournament = Tournament(
        **tournament_data.model_dump(exclude_unset=True),
        club_id=club.id
    )

    db.add(tournament)
    db.commit()
    db.refresh(tournament)

    # Retorno
    return {"message": "Tournament created successfully", "tournament": {
        "id": tournament.id,
        "title": tournament.title,
        "place": tournament.place,
        "start_date": tournament.start_date,
        "end_date": tournament.end_date,
        "time_control": tournament.time_control,
        "rating": tournament.rating,
        "image_url": tournament.image_url,
    }}
