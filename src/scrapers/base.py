import logging
import os
import sys

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from supabase import Client, create_client
from urllib3.util.retry import Retry


class BaseScraper:
    def __init__(self, global_args=None):
        load_dotenv()
        self.logger = self._setup_logging()
        self.supabase = self._get_supabase()
        self.session = self._get_session()
        # Argumentos globais (ex: max_pages)
        self.args = global_args or {}
        self.max_pages = int(self.args.get("max_pages", 999))

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        # O nome do logger será o nome da classe que herdar
        return logging.getLogger(self.__class__.__name__)

    def _get_supabase(self) -> Client:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SECRET_KEY")
        if not url or not key:
            raise ValueError("Credenciais Supabase ausentes.")
        return create_client(url, key)

    def _get_session(self):
        session = requests.Session()
        retry = Retry(
            total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504]
        )
        session.mount("https://", HTTPAdapter(max_retries=retry))
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        return session

    def save(self, table: str, data: list, pk: str = "link"):
        """Método de salvamento que todos os scrapers usarão."""
        if not data:
            return
        try:
            self.supabase.table(table).upsert(data, on_conflict=pk).execute()
            self.logger.info(f"Salvos {len(data)} registros em {table}.")
        except Exception as e:
            self.logger.critical(f"Erro ao salvar em {table}: {e}")

    def run(self):
        """Método que será sobrescrito nas classes filhas."""
        raise NotImplementedError(
            "O método run() deve ser implementado pelo scraper específico."
        )
