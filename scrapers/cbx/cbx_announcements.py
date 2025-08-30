import re
import requests
from fastapi import APIRouter, HTTPException
from bs4 import BeautifulSoup
from typing import List, Optional
from core.utils import get_hidden_fields

router = APIRouter(prefix="/comunicados", tags=["comunicados"])

BASE_URL        = 'https://www.cbx.org.br'
COMUNICADOS_URL = f'{BASE_URL}/comunicados'

def scrape_comunicados(max_pages: Optional[int] = None) -> List[dict]:
    session = requests.Session()
    resp = session.get(COMUNICADOS_URL)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erro ao acessar página de comunicados")
    soup = BeautifulSoup(resp.text, 'html.parser')
    hidden = get_hidden_fields(soup)

    def extract_pages(soup):
        pages = set()
        for a in soup.find_all("a", href=True):
            m = re.search(r"Page\$(\d+)", a["href"])
            if m:
                pages.add(int(m.group(1)))
        return pages

    first_pages = extract_pages(soup) | {1}
    if max_pages:
        pages_to_visit = [p for p in sorted(first_pages) if p <= max_pages]
    else:
        pages_to_visit = sorted(first_pages)

    visited = set()
    comunicados = []

    while pages_to_visit:
        page = pages_to_visit.pop(0)
        if page in visited:
            continue
        visited.add(page)

        if page > 1:
            post_data = {
                **hidden,
                "__EVENTTARGET": "ctl00$ContentPlaceHolder1$gdvMain",
                "__EVENTARGUMENT": f"Page${page}",
            }
            resp = session.post(COMUNICADOS_URL, data=post_data)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"Erro na página {page}")
            soup = BeautifulSoup(resp.text, 'html.parser')
            hidden = get_hidden_fields(soup)

        for a in soup.find_all("a", id=re.compile(r"ContentPlaceHolder1_gdvMain_hlkTitulo_\d+")):
            titulo = a.get_text(strip=True)
            link = BASE_URL + a["href"].strip()
            date_tag = a.find_next_sibling("span", class_="date")
            data_text = date_tag.get_text(strip=True) if date_tag else ""
            comunicados.append({
                "titulo": titulo,
                "data": data_text,
                "link": link
            })

        if not max_pages:
            novas = extract_pages(soup)
            for p in sorted(novas):
                if p not in visited and p not in pages_to_visit:
                    pages_to_visit.append(p)

    return comunicados

@router.get("", response_model=List[dict])
def get_comunicados(paginas: Optional[int] = None):
    """
    Retorna lista de comunicados da CBX. Parâmetro opcional 'paginas' limita quantas páginas serão raspadas.
    """
    return scrape_comunicados(max_pages=paginas)
