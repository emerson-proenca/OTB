import re
import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from typing import Optional
from core.utils import get_hidden_fields, safe_find, safe_link, safe_line, after_colon
from core.schemas import CBXTournamentResponse

router = APIRouter(prefix="/tournaments", tags=["tournaments"])

BASE_URL = "https://www.cbx.org.br"
TOURNAMENTS_URL = f"{BASE_URL}/torneios"

# Abreviação para extração de HTML torneios
CPH = "ContentPlaceHolder1_gdvMain_"

def extract_pages(soup):
    pages = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"Page\$(\d+)", a["href"])
        if m:
            pages.add(int(m.group(1)))
    return pages

def scrape_tournaments(
    year:  Optional[str],
    month: Optional[str],
    limit: Optional[int]
) -> CBXTournamentResponse:
    session = requests.Session()

    # Padrão para year e mês atual se não fornecidos
    now = datetime.now()
    year = year or str(now.year)
    month = month or ""

    # 1) GET inicial
    resp = session.get(TOURNAMENTS_URL)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erro ao acessar a página de torneios.")
    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    # 2) POST para aplicar o filtro de year/mês
    post_data = {
        **hidden,
        "ctl00$ContentPlaceHolder1$cboAno": year,
        "ctl00$ContentPlaceHolder1$cboMes": month,
        "ctl00$ContentPlaceHolder1$btnBuscar": "Buscar"
    }
    resp = session.post(TOURNAMENTS_URL, data=post_data)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erro ao aplicar filtro.")
    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    to_visit = sorted(extract_pages(soup) | {1})
    visited = set()
    tournaments_list = []

    while to_visit:
        page = to_visit.pop(0)
        if page in visited:
            continue
        visited.add(page)

        if page > 1:
            post = {
                **hidden,
                "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$gdvMain",
                "__EVENTARGUMENT": f"Page${page}",
            }
            resp = session.post(TOURNAMENTS_URL, data=post)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            hidden = get_hidden_fields(soup)

        # agenda novas páginas encontradas
        for p in extract_pages(soup):
            if p not in visited and p not in to_visit:
                to_visit.append(p)

        # extrai torneios da página atual
        for i, table in enumerate(soup.find_all("table", class_="torneios")):
            t = {
                "page":           page,
                "name":           safe_find(table, 'span', id=f'{CPH}lblNomeTorneio_{i}'),
                "id":             after_colon(safe_find(table, 'span', id=f'{CPH}lblIDTorneio_{i}')),
                "status":         after_colon(safe_find(table, 'span', id=f'{CPH}lblStatus_{i}')),
                "time_control":   after_colon(safe_find(table, 'span', id=f'{CPH}lblRitmo_{i}')),
                "rating":         after_colon(safe_find(table, 'span', id=f'{CPH}lblRating_{i}')),
                "total_players":  after_colon(safe_find(table, 'span', id=f'{CPH}lblQtJogadores_{i}')),
                "organizer":      after_colon(safe_find(table, 'span', id=f'{CPH}lblOrganizador_{i}')),
                "place":          after_colon(safe_find(table, 'span', id=f'{CPH}lblLocal_{i}')),
                "fide_players":   after_colon(safe_find(table, 'span', id=f'{CPH}lblQtJogadoresFIDE_{i}')),
                "period":         after_colon(safe_find(table, 'span', id=f'{CPH}lblPeriodo_{i}')),
                "observation":    after_colon(safe_line(table, 'span', id=f'{CPH}lblObs_{i}')),
                "regulation":     BASE_URL + safe_link(table, 'a', 'href', id=f'{CPH}hlkTorneio_{i}')
            }
            tournaments_list.append(t)

            # Checagem se atingiu o limite de torneios
            if limit and len(tournaments_list) >= limit:
                return CBXTournamentResponse(cbx=tournaments_list)
            
    return CBXTournamentResponse(cbx=tournaments_list)


@router.get("", response_model=CBXTournamentResponse)
def get_tournaments(
    year:  Optional[str] = Query(None, min_length=4, max_length=4, description="Desired year, eg: 2025"),
    month: Optional[str] = Query(None, min_length=1, max_length=2, description="Number of the month (1-12), eg: 5 for May"),
    limit: Optional[int] = Query(None, ge=1, description="Max number of tournaments to return")
):
    """
    Returns the number of CBX tournaments filtered by year and month.
    """
    return scrape_tournaments(year, month, limit)
