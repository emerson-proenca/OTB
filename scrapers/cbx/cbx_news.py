import re
import requests
from fastapi import APIRouter, HTTPException
from bs4 import BeautifulSoup
from typing import List, Optional
from core.utils import get_hidden_fields

router = APIRouter(prefix="/noticias", tags=["notícias"])

BASE_URL     = 'https://www.cbx.org.br'
NOTICIAS_URL = f'{BASE_URL}/noticias'


def scrape_noticias(max_pages: Optional[int] = None) -> List[dict]:
    session = requests.Session()
    resp = session.get(NOTICIAS_URL)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erro ao acessar página de notícias")
    soup = BeautifulSoup(resp.text, 'html.parser')
    hidden = get_hidden_fields(soup)

    page_numbers = [int(a.text) for a in soup.find_all("a", href=True) if a.text.isdigit()]
    num_pages = max(page_numbers) if page_numbers else 1
    if max_pages:
        num_pages = min(num_pages, max_pages)

    noticias = []
    for page in range(1, num_pages + 1):
        if page > 1:
            post_data = {
                **hidden,
                "__EVENTTARGET": "ctl00$ContentPlaceHolder1$gdvMain",
                "__EVENTARGUMENT": f"Page${page}",
            }
            resp = session.post(NOTICIAS_URL, data=post_data)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"Erro na página {page}")
            soup = BeautifulSoup(resp.text, 'html.parser')
            hidden = get_hidden_fields(soup)

        links = soup.find_all(
            "a",
            id=re.compile(r"ContentPlaceHolder1_gdvMain_hlkTitulo_\d+")
        )
        for a in links:
            titulo = a.get_text(strip=True)
            link = BASE_URL + a["href"].strip()
            date_tag = a.find_next_sibling("span", class_="date")
            data = date_tag.get_text(strip=True) if date_tag else ""
            noticias.append({
                "titulo": titulo,
                "data": data,
                "link": link
            })
    return noticias

@router.get("", response_model=List[dict])
def get_noticias(paginas: Optional[int] = None):
    """
    Retorna lista de notícias da CBX. Parâmetro opcional 'paginas' limita quantas páginas serão raspadas.
    """
    return scrape_noticias(max_pages=paginas)

