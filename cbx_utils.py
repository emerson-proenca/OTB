import logging
import os
import re
import sys

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from supabase import Client, create_client
from urllib3.util.retry import Retry


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)


def get_supabase() -> Client:
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SECRET_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL ou SUPABASE_SECRET_KEY não encontradas no .env")
    return create_client(url, key)


def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    return session


def get_asp_vars(soup: BeautifulSoup):
    """Extrai campos ocultos do WebForms com segurança."""

    def extract(id_name):
        tag = soup.find("input", id=id_name)
        return tag.get("value", "") if tag else None

    return {
        "__VIEWSTATE": extract("__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": extract("__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": extract("__EVENTVALIDATION"),
    }


def save_data(supabase: Client, table: str, data: list, pk: str):
    """Upsert genérico para Supabase."""
    if not data:
        return
    logger = setup_logging()
    try:
        supabase.table(table).upsert(data, on_conflict=pk).execute()
    except Exception as e:
        logger.critical(f"Erro ao salvar em {table}: {e}")


def safe(element) -> str | None:
    """Extrai o texto após o rótulo (ex: 'Local: Rio' -> 'Rio')."""
    if not element:
        return None
    match = re.search(r".*?:\s*(.*)", element.text)
    return match.group(1).strip() if match else element.text.strip()


def get_text(field):
    
    return safe(
        soup.find("span", id=re.compile(f"ContentPlaceHolder1_gdvMain_{field}_{i}"))
    )