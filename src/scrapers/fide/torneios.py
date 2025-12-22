import asyncio
import json
import time

import aiohttp
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper


class ScraperFideTorneios(BaseScraper):
    def __init__(self, data_args=None, site_args=None, global_args=None):
        super().__init__(global_args)
        self.data_args = data_args or {}
        self.table_name = "fide_tournaments"
        self.base_url = "https://ratings.fide.com"

        # Headers específicos da FIDE
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": f"{self.base_url}/rated_tournaments.phtml",
            "X-Requested-With": "XMLHttpRequest",
        }

    async def _fetch_html(self, session, url):
        """Busca conteúdo de forma assíncrona."""
        try:
            async with session.get(url, headers=self.headers, timeout=30) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            self.logger.error(f"Erro ao buscar {url}: {e}")
            return None

    async def _process_period(self, session, country, period):
        """Lógica de extração de um período específico (vinda do seu código)."""
        timestamp = int(time.time() * 1000)
        url = f"{self.base_url}/a_tournaments.php?country={country}&period={period}&_={timestamp}"

        json_text = await self._fetch_html(session, url)
        if not json_text:
            return []

        try:
            data = json.loads(json_text)
            tournaments = []
            for item in data.get("data", []):
                # ... (Sua lógica original de parsing com BeautifulSoup aqui) ...
                # Simplificado para o exemplo:
                tournaments.append(
                    {
                        "fide_id": item[0],
                        "name": BeautifulSoup(item[1], "html.parser").get_text(
                            strip=True
                        ),
                        "country": country,
                        "period": period,
                    }
                )

            # Salvamento usando o self.save da Base (síncrono, mas ok aqui)
            if tournaments:
                self.save(self.table_name, tournaments, pk="fide_id")
            return len(tournaments)
        except Exception as e:
            self.logger.error(f"Erro no parsing {country}/{period}: {e}")
            return 0

    async def _async_main(self):
        """Orquestrador assíncrono interno."""
        country_input = self.data_args.get("country")
        period_input = self.data_args.get("period")

        if not country_input or not period_input:
            raise ValueError(
                "Argumentos 'country' e 'period' são obrigatórios para FIDE."
            )

        async with aiohttp.ClientSession() as session:
            # Lógica para determinar quais países e períodos processar
            countries = [country_input]  # Implementar logic de "*" se necessário
            periods = [period_input]  # Implementar logic de "*" se necessário

            tasks = []
            for c in countries:
                for p in periods:
                    tasks.append(self._process_period(session, c, p))

            results = await asyncio.gather(*tasks)
            self.logger.info(f"Total de torneios FIDE processados: {sum(results)}")

    def run(self):
        """Ponto de entrada síncrono compatível com o Dispatcher."""
        try:
            # Roda o loop assíncrono dentro do método síncrono
            asyncio.run(self._async_main())
        except Exception as e:
            self.logger.critical(f"Erro crítico no Scraper FIDE: {e}", exc_info=True)
