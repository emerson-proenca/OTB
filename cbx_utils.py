import os
import logging
import requests
import re
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)


def get_supabase() -> Client:
    load_dotenv()
    return create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SECRET_KEY'])


def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    return session


def get_asp_vars(soup: BeautifulSoup):
    """Extrai campos ocultos do WebForms com segurança."""
    def extract(id_name):
        tag = soup.find('input', id=id_name)
        return tag.get('value', '') if tag else ''

    return {
        '__VIEWSTATE': extract('__VIEWSTATE'),
        '__VIEWSTATEGENERATOR': extract('__VIEWSTATEGENERATOR'),
        '__EVENTVALIDATION': extract('__EVENTVALIDATION'),
    }


def save_data(supabase: Client, table: str, data: list, pk: str):
    """Upsert genérico para Supabase."""
    if not data: return
    try:
        supabase.table(table).upsert(data, on_conflict=pk).execute()
    except Exception as e:
        print(f"Erro ao salvar em {table}: {e}")


def safe(element) -> str | None:
    """Extrai o texto após o rótulo (ex: 'Local: Rio' -> 'Rio')."""
    if not element:
        return None
    match = re.search(r'.*?:\s*(.*)', element.text)
    return match.group(1).strip() if match else element.text.strip()
