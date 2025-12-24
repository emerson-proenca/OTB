import asyncio
import re

import aiohttp
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper


class ScraperChessresultsTorneios(BaseScraper):
    def __init__(self, data_args=None, global_args=None, site_args=None):
        super().__init__(global_args)
        self.data_args = data_args or {}
        self.table_name = "chess_results_torneios"
        self.domains = ["https://s1.chess-results.com", "https://s2.chess-results.com"]
        self.search_path = "/TurnierSuche.aspx?lan=1"
        self.semaphore = asyncio.Semaphore(10)

    async def get_asp_vars(self, html):
        soup = BeautifulSoup(html, "html.parser")

        def extract(id_name):
            tag = soup.find("input", {"id": id_name})
            return tag.get("value", "") if tag else ""

        return {
            "__VIEWSTATE": extract("__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": extract("__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": extract("__EVENTVALIDATION"),
            "__LASTFOCUS": extract("__LASTFOCUS"),
        }

    def _extract_table_data(self, soup, domain):
        results = []
        # Procura as linhas de dados da tabela (CRg1 e CRg2)
        rows = soup.find_all("tr", class_=re.compile(r"CRg[12]$"))
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 19:
                continue
            link_tag = cols[1].find("a")
            results.append(
                {
                    "tournament": link_tag.get_text(strip=True)
                    if link_tag
                    else cols[1].text.strip(),
                    "link": f"{domain}/{link_tag['href']}" if link_tag else None,
                    "fed": cols[2].get_text(strip=True),
                    "last_update": cols[4].get_text(strip=True),
                    "start_date": cols[5].get_text(strip=True),
                    "end_date": cols[6].get_text(strip=True),
                    "location": cols[12].get_text(strip=True),
                    "time_control": cols[13].get_text(strip=True),
                    "director": cols[12].get_text(strip=True),
                    "organizer": cols[13].get_text(strip=True),
                    "chief_arbiter": cols[12].get_text(strip=True),
                    "dbkey": cols[18].get_text(strip=True),
                    "event_id": cols[19].get_text(strip=True)
                    if len(cols) > 19
                    else None,
                }
            )
        return results

    async def fetch_id(self, session, tournament_id, domain_idx):
        domain = self.domains[domain_idx % 2]
        url = f"{domain}{self.search_path}"

        async with self.semaphore:
            try:
                self.logger.info(f"Processando ID: {tournament_id}")

                # 1. Carrega a página para pegar variáveis de estado (ASP.NET)
                async with session.get(url) as resp:
                    payload = await self.get_asp_vars(await resp.text())

                # 2. Executa a busca exata pelo ID
                payload.update(
                    {
                        "ctl00$P1$txt_tnr": str(tournament_id),
                        "ctl00$P1$cb_suchen": "Search",
                    }
                )

                async with session.post(url, data=payload) as resp:
                    res_html = await resp.text()

                    if "No tournament was found" in res_html:
                        return None

                    soup = BeautifulSoup(res_html, "html.parser")
                    return self._extract_table_data(soup, domain)

            except Exception as e:
                self.logger.error(f"Falha no ID {tournament_id}: {str(e)}")
                return None

    async def run(self):
        start_id = int(self.data_args.get("start_id", 1_300_001))
        end_id = int(self.data_args.get("end_id", start_id + 1_400_000))
        chunk_size = 100

        async with aiohttp.ClientSession() as session:
            for i in range(start_id, end_id + 1, chunk_size):
                curr_end = min(i + chunk_size - 1, end_id)
                tasks = [
                    self.fetch_id(session, tid, idx)
                    for idx, tid in enumerate(range(i, curr_end + 1))
                ]

                results = await asyncio.gather(*tasks)
                flat_data = [item for sublist in results if sublist for item in sublist]

                if flat_data:
                    # Persistência via BaseScraper
                    self.save(self.table_name, flat_data, pk="dbkey")
                    self.logger.info(
                        f"UPSERT: {len(flat_data)} registros salvos (Range {i}-{curr_end})"
                    )
                else:
                    self.logger.info(f"Lote {i}-{curr_end}: Nenhum torneio encontrado.")

        self.logger.info("Fim da execução Brute-Force.")
