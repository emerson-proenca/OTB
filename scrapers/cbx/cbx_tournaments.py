# Substitua/cole esta função em scrapers/cbx/cbx_tournaments.py
import time
import logging
import re
from typing import Optional, List, Dict
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from core.utils import get_hidden_fields, safe_find, safe_link, safe_line, after_colon

# --- coloque isto logo abaixo dos imports no scrapers/cbx/cbx_tournaments.py ---

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# opcional: já existe logger no arquivo; caso não exista, cria um
logger = logging.getLogger("scraper_cbx")
logger.setLevel(logging.INFO)

def _build_session(retries: int = 3, backoff: float = 1.0, connect_timeout: int = 5, read_timeout: int = 60) -> requests.Session:
    """
    Cria uma requests.Session com Retry/Adapter, headers e timeouts (connect, read).
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
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.cbx.org.br/",
    })

    # armazenamos timeouts na sessão para o wrapper usar
    session._connect_timeout = connect_timeout
    session._read_timeout = read_timeout
    return session

def _safe_request(session: requests.Session, method: str, url: str, **kwargs) -> requests.Response:
    """
    Wrapper que aplica timeout (connect, read) e faz raise para erros HTTP.
    Retorna requests.Response ou levanta requests.exceptions.RequestException.
    """
    connect_to = getattr(session, "_connect_timeout", 5)
    read_to = getattr(session, "_read_timeout", 60)
    # permite sobrescrever timeout via kwargs, caso envie um tuple
    timeout_tuple = kwargs.pop("timeout", (connect_to, read_to))
    start = time.monotonic()
    resp = session.request(method, url, timeout=timeout_tuple, **kwargs)
    duration = time.monotonic() - start
    logger.debug(f"HTTP {method} {url} -> {getattr(resp, 'status_code', 'ERR')} in {duration:.2f}s")
    resp.raise_for_status()
    return resp

# --- fim do trecho a colar ---


BASE_URL = "https://www.cbx.org.br"
TOURNAMENTS_URL = f"{BASE_URL}/torneios"
CPH = "ContentPlaceHolder1_gdvMain_"

# Assumo que _build_session and _safe_request já existem nesse arquivo (use as versões com tuple timeout)
# se não existirem, copie-as do trecho anterior que trocamos.

def extract_pages(soup):
    pages = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"Page\$(\d+)", a["href"])
        if m:
            pages.add(int(m.group(1)))
    return pages

def fetch_tournaments_raw(year: Optional[str] = None, month: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
    """
    Função robusta para coletar torneios CBX.
    - Usa GET inicial rápido.
    - Tenta POST de busca (ano/mes). Se POST falhar, usa HTML do GET inicial (fallback).
    - Para paginação, tenta POST para cada página com retries e sleep; se persistir falha, interrompe paginação.
    """
    session = _build_session(retries=3, backoff=1.0, connect_timeout=5, read_timeout=60)
    now = datetime.now()
    year = year or str(now.year)
    month = month or ""

    # 1) GET inicial (rápido) — já temos o HTML básico
    try:
        resp = _safe_request(session, "GET", TOURNAMENTS_URL)
    except requests.exceptions.RequestException as e:
        logger.exception("GET inicial falhou — abortando fetch_tournaments_raw")
        raise

    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    # 2) Tentar POST de busca (ano/mes). Se falhar, usamos o soup do GET inicial.
    post_data = {
        **hidden,
        "ctl00$ContentPlaceHolder1$cboAno": year,
        "ctl00$ContentPlaceHolder1$cboMes": month,
        "ctl00$ContentPlaceHolder1$btnBuscar": "Buscar"
    }

    tried_post = False
    try:
        tried_post = True
        resp = _safe_request(session, "POST", TOURNAMENTS_URL, data=post_data)
        soup = BeautifulSoup(resp.text, "html.parser")
        hidden = get_hidden_fields(soup)
    except requests.exceptions.RequestException as e:
        # Falha no POST — log e fallback para HTML do GET inicial (já em `soup`)
        logger.warning("POST de busca falhou (possível lentidão do servidor). Usando HTML do GET inicial como fallback.")
        # não raise, continuamos com 'soup' do GET inicial

    # 3) Monta páginas a visitar
    to_visit = sorted(extract_pages(soup) | {1})
    visited = set()
    tournaments_list = []

    # parâmetros de tentativa por página
    max_page_attempts = 3
    sleep_between_attempts = 2  # segundos

    while to_visit:
        page = to_visit.pop(0)
        if page in visited:
            continue
        visited.add(page)

        # se page > 1 e tentamos POST originalmente, seguimos a lógica de post por paginação
        if page > 1:
            # para cada página tentamos até max_page_attempts vezes
            attempt = 0
            page_success = False
            while attempt < max_page_attempts and not page_success:
                attempt += 1
                try:
                    post = {
                        **hidden,
                        "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$gdvMain",
                        "__EVENTARGUMENT": f"Page${page}",
                    }
                    resp = _safe_request(session, "POST", TOURNAMENTS_URL, data=post)
                    soup = BeautifulSoup(resp.text, "html.parser")
                    hidden = get_hidden_fields(soup)
                    page_success = True
                    # respeitar um pequeno atraso entre páginas para reduzir chances de throttling
                    time.sleep(0.5)
                except requests.exceptions.RequestException:
                    logger.warning(f"Falha ao buscar página {page} (attempt {attempt}/{max_page_attempts}). Retentando após sleep.")
                    time.sleep(sleep_between_attempts * attempt)  # backoff linear
                except Exception:
                    logger.exception(f"Erro inesperado ao buscar página {page} (attempt {attempt}).")
                    time.sleep(sleep_between_attempts)

            if not page_success:
                logger.error(f"Não foi possível recuperar página {page} após {max_page_attempts} tentativas. Interrompendo paginação.")
                break  # evita travar o job inteiro — a gente já trouxe o que pôde

        # descobrir novas páginas (só faz sentido se page_success ou page==1)
        for p in extract_pages(soup):
            if p not in visited and p not in to_visit:
                to_visit.append(p)

        # parse das tabelas da página atual
        for i, table in enumerate(soup.find_all("table", class_="torneios")):
            try:
                t = {
                    "page":           page,
                    "name":           safe_find(table, 'span', id=f'{CPH}lblNomeTorneio_{i}'),
                    "external_id":    after_colon(safe_find(table, 'span', id=f'{CPH}lblIDTorneio_{i}')),
                    "status":         after_colon(safe_find(table, 'span', id=f'{CPH}lblStatus_{i}')),
                    "time_control":   after_colon(safe_find(table, 'span', id=f'{CPH}lblRitmo_{i}')),
                    "rating":         after_colon(safe_find(table, 'span', id=f'{CPH}lblRating_{i}')),
                    "total_players":  after_colon(safe_find(table, 'span', id=f'{CPH}lblQtJogadores_{i}')),
                    "organizer":      after_colon(safe_find(table, 'span', id=f'{CPH}lblOrganizador_{i}')),
                    "place":          after_colon(safe_find(table, 'span', id=f'{CPH}lblLocal_{i}')),
                    "fide_players":   after_colon(safe_find(table, 'span', id=f'{CPH}lblQtJogadoresFIDE_{i}')),
                    "period":         after_colon(safe_find(table, 'span', id=f'{CPH}lblPeriodo_{i}')),
                    "observation":    after_colon(safe_line(table, 'span', id=f'{CPH}lblObs_{i}')),
                    "regulation":     BASE_URL + safe_link(table, 'a', 'href', id=f'{CPH}hlkTorneio_{i}'),
                    "federation":     "cbx",
                    "year": year,
                    "month": month or ""
                }
                tournaments_list.append(t)
                if limit and len(tournaments_list) >= limit:
                    return tournaments_list
            except Exception:
                logger.exception("Erro ao parsear uma entrada de torneio — pulando essa entrada.")
                continue

    return tournaments_list
