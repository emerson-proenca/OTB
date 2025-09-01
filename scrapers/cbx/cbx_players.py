# scrapers/cbx/cbx_players.py
import re
import time
import logging
from typing import List, Optional, Dict
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from core.utils import get_hidden_fields

logger = logging.getLogger("scraper_cbx_players")
logger.setLevel(logging.INFO)

BASE_URL = "https://www.cbx.org.br"
URL = f"{BASE_URL}/rating"

def _build_session(retries: int = 3, backoff: float = 1.0, connect_timeout: int = 5, read_timeout: int = 60) -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({
        "User-Agent": "OverTheBoardBot/1.0 (+https://github.com/Emersh0w/Over-The-Board)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": BASE_URL + "/",
    })

    session._connect_timeout = connect_timeout
    session._read_timeout = read_timeout
    return session

def _safe_request(session: requests.Session, method: str, url: str, **kwargs) -> requests.Response:
    connect_to = getattr(session, "_connect_timeout", 5)
    read_to = getattr(session, "_read_timeout", 60)
    timeout_tuple = kwargs.pop("timeout", (connect_to, read_to))
    start = time.monotonic()
    resp = session.request(method, url, timeout=timeout_tuple, **kwargs)
    duration = time.monotonic() - start
    logger.debug(f"HTTP {method} {url} -> {getattr(resp, 'status_code', 'ERR')} in {duration:.2f}s")
    resp.raise_for_status()
    return resp

def _extract_pages(soup: BeautifulSoup) -> List[int]:
    pages = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"Page\$(\d+)", a["href"])
        if m:
            pages.add(int(m.group(1)))
    return sorted(pages)

def fetch_players_raw(state: str = "SP", max_pages: Optional[int] = None) -> List[Dict]:
    """
    Faz scraping dos jogadores da CBX para um estado e retorna lista de dicts.
    NÃO lança fastapi.HTTPException — levanta requests.exceptions.RequestException em erros de rede.
    """
    session = _build_session(retries=3, backoff=1.0, connect_timeout=5, read_timeout=60)

    # GET inicial
    resp = _safe_request(session, "GET", URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    # POST para filtrar por estado (UF)
    payload = {
        **hidden,
        "ctl00$ContentPlaceHolder1$cboUF": state,
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$cboUF",
        "__EVENTARGUMENT": "",
        "ctl00$ContentPlaceHolder1$btnBuscar": "Buscar"
    }

    resp = _safe_request(session, "POST", URL, data=payload)
    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    pages_to_visit = sorted(set(_extract_pages(soup)) | {1})
    if max_pages:
        pages_to_visit = [p for p in pages_to_visit if p <= max_pages]

    visited = set()
    players: List[Dict] = []

    while pages_to_visit:
        page = pages_to_visit.pop(0)
        if page in visited:
            continue
        visited.add(page)

        if page > 1:
            post = {
                **hidden,
                "__EVENTTARGET": "ctl00$ContentPlaceHolder1$gdvMain",
                "__EVENTARGUMENT": f"Page${page}",
            }
            try:
                resp = _safe_request(session, "POST", URL, data=post)
            except Exception:
                logger.exception(f"Falha ao recuperar pagina {page}; interrompendo paginação.")
                break
            soup = BeautifulSoup(resp.text, "html.parser")
            hidden = get_hidden_fields(soup)

        table = soup.find("table", class_="grid")
        if not table:
            continue

        rows = table.find_all("tr", recursive=False)
        if not rows:
            continue

        headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]

        for row in rows[1:]:
            if "grid-pager" in row.get("class", []):
                continue
            cells = row.find_all("td")
            if not cells:
                continue
            vals = [td.get_text(strip=True) for td in cells]
            rec = dict(zip(headers, vals))

            cbx_id = rec.get("ID CBX", "") or ""
            link = f"{BASE_URL}/jogador/{cbx_id}" if cbx_id else ""
            player = {
                "local_id": cbx_id,
                "name": rec.get("Nome", ""),
                "birthday": rec.get("Data Nasc.", ""),
                "gender": "",  # not provided
                "country": "Brasil",
                "state": rec.get("UF", ""),
                "classical": rec.get("Clássico", ""),
                "rapid": rec.get("Rápido", ""),
                "blitz": rec.get("Blitz", ""),
                "fide_id": rec.get("ID FIDE", ""),
                "local_profile": link,
                "scraped_at": datetime.utcnow().isoformat()  # raw value; job can overwrite with timezone-aware
            }
            players.append(player)

        # discover new pages if not limited
        if not max_pages:
            novas = _extract_pages(soup)
            for p in sorted(novas):
                if p not in visited and p not in pages_to_visit:
                    pages_to_visit.append(p)

    return players
