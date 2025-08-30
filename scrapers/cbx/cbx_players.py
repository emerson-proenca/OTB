import re
import requests
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from bs4 import BeautifulSoup
from core.utils import get_hidden_fields
from core.schemas import CBXPlayerResponse

router = APIRouter(prefix="/jogadores", tags=["jogadores"])

BASE_URL = "https://www.cbx.org.br"
URL      = f"{BASE_URL}/rating"

def scrape_players(
    state: str,
    max_pages: Optional[int] = None
) -> List[dict]:
    session = requests.Session()

    # GET inicial
    resp = session.get(URL)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Error accessing players page")
    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    # Postback para filtrar por UF
    payload = {
        **hidden,
        "ctl00$ContentPlaceHolder1$cboUF": state,
        "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$cboUF",
        "__EVENTARGUMENT": "",
        "ctl00$ContentPlaceHolder1$btnBuscar": "Buscar"
    }
    resp = session.post(URL, data=payload)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Error in state filter")
    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    # Função interna para extrair números de página
    def extract_pages(soup):
        pages = set()
        for a in soup.find_all("a", href=True):
            m = re.search(r"Page\$(\d+)", a["href"])
            if m:
                pages.add(int(m.group(1)))
        return pages

    # Descobre páginas a visitar (inclui a 1)
    pages_to_visit = sorted(extract_pages(soup) | {1})
    if max_pages:
        pages_to_visit = [p for p in pages_to_visit if p <= max_pages]

    visited = set()
    players = []

    while pages_to_visit:
        page = pages_to_visit.pop(0)
        if page in visited:
            continue
        visited.add(page)

        # Postback de paginação
        if page > 1:
            post = {
                **hidden,
                "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$gdvMain",
                "__EVENTARGUMENT": f"Page${page}",
            }
            resp = session.post(URL, data=post)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"Erro na página {page}")
            soup = BeautifulSoup(resp.text, "html.parser")
            hidden = get_hidden_fields(soup)

        # Extrai a tabela de jogadores
        table = soup.find("table", class_="grid")
        if not table:
            continue

        rows = table.find_all("tr", recursive=False)
        headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]

        # Para cada linha de dados
        for row in rows[1:]:
            if "grid-pager" in row.get("class", []):
                continue
            cells = row.find_all("td")
            if not cells:
                continue
            vals = [td.get_text(strip=True) for td in cells]
            rec = dict(zip(headers, vals))

            # Adiciona link do jogador
            cbx_id = rec.get("ID CBX", "")
            rec["link"] = f"{BASE_URL}/jogador/{cbx_id}" if cbx_id else ""
            # Criação do JSON
            players.append ({
                "local_id": cbx_id,
                "name": rec.get("Nome",""),
                "birthday": rec.get("Data Nasc.",""),
                # Gender e Country não são fornecidos pela CBX
                "gender": "",
                "country": "Brasil",
                "state": rec.get("UF",""),
                "classical": rec.get("Clássico",""),
                "rapid": rec.get("Rápido",""),
                "blitz": rec.get("Blitz",""),
                "fide_id": rec.get("ID FIDE",""),
                "local_profile": rec["link"]
            })

        # Se não limitamos, agenda novas páginas
        if not max_pages:
            novas = extract_pages(soup)
            for p in sorted(novas):
                if p not in visited and p not in pages_to_visit:
                    pages_to_visit.append(p)

    return CBXPlayerResponse(cbx=players)

@router.get("", response_model=CBXPlayerResponse)
def get_players(
    state: str = Query("SP", min_length=2, max_length=2, description="State abbreviation (eg: SP, RJ)"),
    pages: Optional[int] = Query(None, ge=1, description="Max number of pages to scrape")
):
    """
    Returns the list of players from CBX listed by state.
    - **state**: First 2 letters of the states (2 characters)
    - **pages**: optional, limits the amount of pages to be scraped
    """
    return scrape_players(state=state, max_pages=pages)
