import json
import time
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup
from cbx_utils import get_supabase, setup_logging

# Configuração inicial
logger = setup_logging()
supabase = get_supabase()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://ratings.fide.com/rated_tournaments.phtml",
    "X-Requested-With": "XMLHttpRequest",
}


class SyncFIDEScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch_html(self, url: str) -> str | None:
        """Busca conteúdo HTML/JSON de forma síncrona"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Erro ao buscar {url}: {e}")
            return None

    def fetch_all_country_codes(self) -> List[str]:
        """Extrai todos os códigos de países do dropdown"""
        url = "https://ratings.fide.com/rated_tournaments.phtml"
        html = self.fetch_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        select_country = soup.find("select", {"id": "select_country"})
        if not select_country:
            logger.error("Elemento select_country não encontrado")
            return []

        country_codes = [
            option["value"]
            for option in select_country.find_all("option")
            if option.get("value") and option["value"] != "all"
        ]
        logger.info(f"Encontrados {len(country_codes)} códigos de país")
        return country_codes

    def fetch_available_periods(self, country_code: str) -> List[str]:
        """Busca todos os períodos disponíveis para um país"""
        url = f"https://ratings.fide.com/a_tournaments_panel.php?country={country_code}&periods_tab=1"
        json_text = self.fetch_html(url)
        if not json_text:
            return []

        try:
            periods_data = json.loads(json_text)
            return [item["frl_publish"] for item in periods_data]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Erro ao processar períodos para {country_code}: {e}")
            return []

    def fetch_tournaments_for_period(
        self, country_code: str, period: str
    ) -> List[Dict[str, Any]]:
        """Busca torneios de um período específico"""
        timestamp = int(time.time() * 1000)
        url = f"https://ratings.fide.com/a_tournaments.php?country={country_code}&period={period}&_={timestamp}"
        json_text = self.fetch_html(url)
        if not json_text:
            return []

        try:
            data = json.loads(json_text)
            tournaments = []
            for item in data.get("data", []):
                soup_name = BeautifulSoup(item[1], "html.parser")
                name_link = soup_name.find("a")

                # Parsing do link e nome
                name = name_link.get_text(strip=True) if name_link else item[1]
                # link_event = (name_link["href"]if name_link and "href" in name_link.attrs else None)

                # Parsing do campo Received (índice 5)
                soup_rcvd = (
                    BeautifulSoup(item[5], "html.parser") if len(item) > 5 else None
                )
                rcvd = (
                    soup_rcvd.find("a").get_text(strip=True)
                    if soup_rcvd and soup_rcvd.find("a")
                    else (item[5] if len(item) > 5 else None)
                )

                tournaments.append(
                    {
                        "fide_id": item[0],
                        "name": name,
                        "city": item[2] if len(item) > 2 else None,
                        "s": item[3] if len(item) > 3 else None,
                        "start": item[4] if len(item) > 4 else None,
                        "rcvd": rcvd,
                        "country": country_code,
                        "period": period,
                        # MANTER MAS NÃO ENVIAR:
                        # "link_information": f"https://ratings.fide.com/tournament_information.phtml?event={item[0]}",
                        # "link_event": f"https://ratings.fide.com{link_event}" if link_event else None,
                    }
                )
            return tournaments
        except Exception as e:
            logger.error(f"Erro ao processar torneios {country_code} ({period}): {e}")
            return []

    def upsert_tournaments(self, tournaments: List[Dict[str, Any]]):
        """Faz upsert no Supabase especificando as colunas"""
        if not tournaments:
            return
        try:
            supabase.table("fide_tournaments").upsert(
                tournaments,
                on_conflict="fide_id",  # Ou a PK definida no seu banco
            ).execute()
            logger.info(f"UPSERT: {len(tournaments)} registros processados.")
        except Exception as e:
            logger.error(f"Erro no UPSERT: {e}")

    def run(self, test_mode=False, max_countries=None):
        start_time = time.time()
        country_codes = self.fetch_all_country_codes()

        if test_mode:
            country_codes = country_codes[:5]
        elif max_countries:
            country_codes = country_codes[:max_countries]

        total_tournaments = 0
        for code in country_codes:
            logger.info(f"Processando país: {code}")
            periods = self.fetch_available_periods(code)
            for period in periods:
                tournaments = self.fetch_tournaments_for_period(code, period)
                if tournaments:
                    self.upsert_tournaments(tournaments)
                    total_tournaments += len(tournaments)

        total_time = time.time() - start_time
        logger.info(f"CONCLUÍDO! Torneios: {total_tournaments} em {total_time:.2f}s")


if __name__ == "__main__":
    scraper = SyncFIDEScraper()
    scraper.run(test_mode=True)
