# scrapers/cbx/cbx_announcements.py
import re
import time
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from core.utils import get_hidden_fields

# Exceptions to handle
from requests.exceptions import ChunkedEncodingError, RequestException
from urllib3.exceptions import ProtocolError, ReadTimeoutError
import http.client

logger = logging.getLogger("scraper_cbx_announcements")
logger.setLevel(logging.INFO)

BASE_URL = "https://www.cbx.org.br"
COMUNICADOS_URL = f"{BASE_URL}/comunicados"


def _build_session(retries: int = 3, backoff: float = 1.0, connect_timeout: int = 5, read_timeout: int = 60) -> requests.Session:
    """
    Cria uma Session com Retry adapter; tempos e estratégia padrão.
    """
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


def _safe_request(session: requests.Session, method: str, url: str, retries: int = 3, backoff: float = 1.0, **kwargs) -> requests.Response:
    """
    Wrapper robusto para requests:
    - trata ChunkedEncodingError / ProtocolError / IncompleteRead / ReadTimeoutError
    - implementa backoff exponencial
    - re-levanta a última exceção após esgotar tentativas
    """
    connect_to = getattr(session, "_connect_timeout", 5)
    read_to = getattr(session, "_read_timeout", 60)
    timeout_tuple = kwargs.pop("timeout", (connect_to, read_to))

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            start = time.monotonic()
            resp = session.request(method, url, timeout=timeout_tuple, **kwargs)
            duration = time.monotonic() - start
            logger.debug(f"HTTP {method} {url} -> {getattr(resp, 'status_code', 'ERR')} in {duration:.2f}s")
            resp.raise_for_status()
            return resp
        except (ChunkedEncodingError, ProtocolError, http.client.IncompleteRead, ReadTimeoutError) as e:
            last_exc = e
            logger.warning(f"Stream/network error on attempt {attempt}/{retries} for {url}: {type(e).__name__}: {e}")
        except RequestException as e:
            last_exc = e
            logger.warning(f"RequestException on attempt {attempt}/{retries} for {url}: {type(e).__name__}: {e}")

        if attempt < retries:
            sleep_seconds = backoff * (2 ** (attempt - 1))
            logger.debug(f"Sleeping {sleep_seconds:.1f}s before retry ({attempt}/{retries})")
            time.sleep(sleep_seconds)

    logger.error(f"All {retries} attempts failed for {method} {url}")
    if last_exc:
        raise last_exc
    else:
        raise RequestException("Unknown request error")


def _extract_pages(soup: BeautifulSoup) -> List[int]:
    pages = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"Page\$(\d+)", a["href"])
        if m:
            pages.add(int(m.group(1)))
    return sorted(pages)


def fetch_announcements_raw(max_pages: Optional[int] = None) -> Tuple[List[Dict], List[str]]:
    """
    Faz scraping dos comunicados da CBX e retorna:
      - announcements: List[Dict] com os comunicados coletados
      - failed_pages: List[str] com identificadores/URLs das páginas que falharam

    O scraper é tolerante a falhas em páginas individuais: registra e continua.
    Levanta RequestException somente se a requisição inicial falhar.
    """
    session = _build_session(retries=3, backoff=1.0, connect_timeout=5, read_timeout=60)
    failed_pages: List[str] = []

    # GET inicial — se falhar completamente, propagamos a exceção
    try:
        resp = _safe_request(session, "GET", COMUNICADOS_URL)
    except Exception as e:
        logger.exception("Failed to GET comunicados (initial).")
        raise

    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    pages_to_visit = sorted(set(_extract_pages(soup)) | {1})
    if max_pages:
        pages_to_visit = [p for p in pages_to_visit if p <= max_pages]

    visited = set()
    announcements: List[Dict] = []

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
                resp = _safe_request(session, "POST", COMUNICADOS_URL, data=post_data)
                soup = BeautifulSoup(resp.text, "html.parser")
                hidden = get_hidden_fields(soup)
            except Exception as e:
                page_id = f"{COMUNICADOS_URL}?page={page}"
                failed_pages.append(page_id)
                logger.exception(f"Falha ao recuperar página {page} dos comunicados: {e}. Pulando página.")
                continue

        # seleciona links com pattern do site
        links = soup.find_all("a", id=re.compile(r"ContentPlaceHolder1_gdvMain_hlkTitulo_\d+"))
        if not links:
            continue

        for a in links:
            try:
                title = a.get_text(strip=True)
                href = a.get("href", "").strip()
                link = BASE_URL + href if href.startswith("/") else href
                date_tag = a.find_next_sibling("span", class_="date")
                date_text = date_tag.get_text(strip=True) if date_tag else ""
                # content: tentar buscar um parágrafo próximo ou elemento que contenha o texto do comunicado
                content = ""
                parent = a.find_parent()
                if parent:
                    p_tag = parent.find("p")
                    if p_tag:
                        content = p_tag.get_text(strip=True)
                announcements.append({
                    "title": title,
                    "date_text": date_text,
                    "link": link,
                    "content": content,
                    "scraped_at": datetime.utcnow().isoformat()
                })
            except Exception:
                logger.exception("Erro ao parsear um comunicado; pulando.")

        # discover new pages if not limited
        if not max_pages:
            try:
                novas = _extract_pages(soup)
                for p in sorted(novas):
                    if p not in visited and p not in pages_to_visit:
                        pages_to_visit.append(p)
            except Exception:
                logger.debug("Failed to discover additional pages; continuing with known pages.")

    return announcements, failed_pages
