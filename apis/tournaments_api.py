# apis/tournaments_api.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from core.schemas import CBXTournamentResponse
from database.session import SessionLocal
from database.models import Tournament
import logging

router = APIRouter(prefix="/tournaments", tags=["tournaments"])
logger = logging.getLogger("apis.tournaments")

def _safe_str(v) -> str:
    if v is None:
        return ""
    # evita "None" como string
    return str(v)

def _safe_int_for_page(v) -> int:
    try:
        if v is None:
            return 1
        return int(v)
    except Exception:
        return 1

@router.get("", response_model=CBXTournamentResponse)
def get_tournaments(
    federation: Optional[str] = Query(None, description="Sigla da federação (cbx, fide, uscf…)."),
    year: Optional[str] = Query(None, min_length=4, max_length=4, description="Ano, ex: 2025"),
    month: Optional[str] = Query("", max_length=2, description="Mês (1–12) ou vazio"),
    limit: int = Query(10, ge=1, description="Máximo de torneios a retornar")
):
    db = SessionLocal()
    try:
        q = db.query(Tournament)
        if federation:
            q = q.filter(Tournament.federation == federation.lower())
        if year:
            q = q.filter(Tournament.year == year)
        if month:
            q = q.filter(Tournament.month == month)
        q = q.order_by(Tournament.scraped_at.desc())
        results = q.limit(limit).all()

        cbx = []
        for t in results:
            # normaliza tipos para evitar falhas no Pydantic
            page_val = _safe_int_for_page(getattr(t, "page", None))
            total_players_val = _safe_str(getattr(t, "total_players", ""))  # CBX schema espera string
            fide_players_val = _safe_str(getattr(t, "fide_players", ""))    # se schema espera string
            cbx_item = {
                "page": page_val,
                "name": _safe_str(t.name),
                "id": _safe_str(t.external_id) or "",
                "status": _safe_str(t.status),
                "time_control": _safe_str(t.time_control),
                "rating": _safe_str(t.rating),
                "total_players": total_players_val,
                "organizer": _safe_str(t.organizer),
                "place": _safe_str(t.place),
                "fide_players": fide_players_val,
                "period": _safe_str(t.period),
                "observation": _safe_str(t.observation),
                "regulation": _safe_str(t.regulation),
            }
            cbx.append(cbx_item)

        # Retorna o response_model — agora os itens estão tipados corretamente.
        return CBXTournamentResponse(cbx=cbx)
    except Exception as e:
        logger.exception("Erro ao construir resposta de torneios")
        # devolve 500 com mensagem curta — detalhes estarão nos logs
        raise HTTPException(status_code=500, detail="Internal server error building tournament response")
    finally:
        db.close()
