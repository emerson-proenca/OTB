# scrapers/cbx/cbx_news.py
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

logger = logging.getLogger("scraper_cbx_news")
logger.setLevel(logging.INFO)

BASE_URL = "https://www.cbx.org.br"
NOTICIAS_URL = f"{BASE_URL}/noticias"

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

def fetch_news_raw(max_pages: Optional[int] = None) -> List[Dict]:
    """
    Faz scraping das notícias da CBX e retorna lista de dicts:
    [{ "title": ..., "date_text": ..., "link": ..., "summary": ... }, ...]
    Levanta requests.exceptions.RequestException em caso de problemas de rede.
    """
    session = _build_session(retries=3, backoff=1.0, connect_timeout=5, read_timeout=60)

    resp = _safe_request(session, "GET", NOTICIAS_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    pages_to_visit = sorted(set(_extract_pages(soup)) | {1})
    if max_pages:
        pages_to_visit = [p for p in pages_to_visit if p <= max_pages]

    visited = set()
    news: List[Dict] = []

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
            try:
                resp = _safe_request(session, "POST", NOTICIAS_URL, data=post_data)
            except Exception:
                logger.exception(f"Falha ao recuperar página {page} de notícias; interrompendo paginação.")
                break
            soup = BeautifulSoup(resp.text, "html.parser")
            hidden = get_hidden_fields(soup)

        links = soup.find_all("a", id=re.compile(r"ContentPlaceHolder1_gdvMain_hlkTitulo_\d+"))
        for a in links:
            try:
                title = a.get_text(strip=True)
                href = a.get("href", "").strip()
                link = BASE_URL + href if href.startswith("/") else href
                date_tag = a.find_next_sibling("span", class_="date")
                date_text = date_tag.get_text(strip=True) if date_tag else ""
                # optional summary: find a sibling <p> or next <div>
                summary_tag = a.find_parent().find("p")
                summary = summary_tag.get_text(strip=True) if summary_tag else ""
                news.append({
                    "title": title,
                    "date_text": date_text,
                    "link": link,
                    "summary": summary,
                    "scraped_at": datetime.utcnow().isoformat()
                })
            except Exception:
                logger.exception("Erro ao parsear uma notícia; pulando.")

        if not max_pages:
            novas = _extract_pages(soup)
            for p in sorted(novas):
                if p not in visited and p not in pages_to_visit:
                    pages_to_visit.append(p)

    return news
