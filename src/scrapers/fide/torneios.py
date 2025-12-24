import json
import time
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper


class SyncFIDEScraper(BaseScraper):
    def __init__(self, global_args=None):
        super().__init__(global_args)

        self.session.headers.update(
            {
                "Referer": "https://ratings.fide.com/rated_tournaments.phtml",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

    def fetch_html(self, url: str) -> str | None:
        """Busca conteúdo utilizando a sessão com retentativas da classe pai."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Erro ao buscar {url}: {e}")
            return None

    def fetch_all_country_codes(self) -> List[str]:
        """Extrai todos os códigos de países do dropdown."""
        url = "https://ratings.fide.com/rated_tournaments.phtml"
        html = self.fetch_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        select_country = soup.find("select", {"id": "select_country"})
        if not select_country:
            self.logger.error("Elemento select_country não encontrado")
            return []

        return [
            option["value"]
            for option in select_country.find_all("option")
            if option.get("value") and option["value"] != "all"
        ]

    def fetch_available_periods(self, country_code: str) -> List[str]:
        """Busca períodos disponíveis para um país."""
        url = f"https://ratings.fide.com/a_tournaments_panel.php?country={country_code}&periods_tab=1"
        json_text = self.fetch_html(url)
        if not json_text:
            return []

        try:
            periods_data = json.loads(json_text)
            return [item["frl_publish"] for item in periods_data]
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Erro ao processar períodos para {country_code}: {e}")
            return []

    def fetch_tournaments_for_period(
        self, country_code: str, period: str
    ) -> List[Dict[str, Any]]:
        """Busca e faz o parsing dos torneios de um período."""
        timestamp = int(time.time() * 1000)
        url = f"https://ratings.fide.com/a_tournaments.php?country={country_code}&period={period}&_={timestamp}"
        json_text = self.fetch_html(url)
        if not json_text:
            return []

        try:
            data = json.loads(json_text)
            tournaments = []
            for item in data.get("data", []):
                # Parsing do nome e link
                soup_name = BeautifulSoup(item[1], "html.parser")
                name_link = soup_name.find("a")
                name = name_link.get_text(strip=True) if name_link else item[1]

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
                    }
                )
            return tournaments
        except Exception as e:
            self.logger.error(
                f"Erro ao processar torneios {country_code} ({period}): {e}"
            )
            return []


def run(self):
    country = self.data_args.get("country")
    if not country:
        raise ValueError("O argumento 'country' é obrigatório para ChessResults.")

    self.logger.info(f"Iniciando Chess-Results para país: {country}")

    # 1. GET inicial para pegar tokens
    res = self.session.get(self.url)
    soup = BeautifulSoup(res.text, "html.parser")

    # 2. Payload simulando o clique no botão "Search"
    payload = self.get_asp_vars(soup)
    payload.update(
        {
            # Importante: O botão de busca precisa estar no payload para o ASP processar
            "ctl00$P1$combo_land": country,
            "ctl00$P1$combo_anzahl_zeilen": "5",  # 2000 linhas
            "ctl00$P1$cb_incl_old_tournaments": "on",
            "ctl00$P1$button_suchen": "Search",  # Simula o clique no botão
            "__EVENTTARGET": "",  # No clique do botão, o target costuma ser vazio
            "__EVENTARGUMENT": "",
        }
    )

    # 3. POST para submeter a busca real
    res = self.session.post(self.url, data=payload)
    soup = BeautifulSoup(res.text, "html.parser")

    # DEBUG: Se quiser ver se a tabela existe no HTML retornado:
    # self.logger.info(f"Tamanho do HTML: {len(res.text)}")

    tournaments = self._extract_table_data(soup)

    if tournaments:
        self.save(self.table_name, tournaments, pk="dbkey")
        self.logger.info(f"Sucesso: {len(tournaments)} torneios processados.")
    else:
        self.logger.warning(
            "Nenhum torneio encontrado. Verifique se o Seletor CSS 'CRg2' ainda é válido."
        )


if __name__ == "__main__":
    # Exemplo com argumentos globais
    args = {"test_mode": True, "max_pages": 3}
    scraper = SyncFIDEScraper(global_args=args)
    scraper.run()
