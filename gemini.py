import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

import aiohttp
from bs4 import BeautifulSoup

# Configuração refinada
CONFIG = {
    "START": "2024-01-01",
    "END": "",
    "COUNTRIES": [],
    "CONCURRENCY": 5,
    "FILE": "fide_data.jsonl",
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def parse_fide_date(ds: str) -> Optional[datetime]:
    if not ds or ds == "0000-00-00":
        return None
    try:
        return datetime.strptime(ds, "%Y-%m-%d")
    except ValueError:
        return None


class FideScraper:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.sem = asyncio.Semaphore(CONFIG["CONCURRENCY"])
        self.base_url = "https://ratings.fide.com"

    async def fetch_countries(self) -> List[str]:
        async with self.session.get(f"{self.base_url}/rated_tournaments.phtml") as r:
            soup = BeautifulSoup(await r.text(), "lxml")
            select = soup.select_one("#select_country")
            if not select:
                return []
            return [
                o["value"]
                for o in select.find_all("option")
                if o.get("value") not in (None, "all")
            ]

    async def get_periods(self, country: str) -> List[str]:
        async with self.sem:
            url = f"{self.base_url}/a_tournaments_panel.php"
            async with self.session.get(
                url, params={"country": country, "periods_tab": 1}
            ) as r:
                data = await r.json(content_type=None)
                return [p["frl_publish"] for p in data]

    async def scrape_tournament_batch(self, country: str, period: str, out_file):
        async with self.sem:
            url = f"{self.base_url}/a_tournaments.php"
            params = {"country": country, "period": period}

            async with self.session.get(url, params=params) as r:
                payload = await r.json(content_type=None)
                count = 0

                for row in payload.get("data", []):
                    # Garante que a linha tenha colunas suficientes
                    row += [None] * (6 - len(row))
                    start_date = row[4]

                    # Filtro de data simplificado
                    dt = parse_fide_date(start_date)
                    if dt:
                        if CONFIG["START"] and dt < datetime.strptime(
                            CONFIG["START"], "%Y-%m-%d"
                        ):
                            continue
                        if CONFIG["END"] and dt > datetime.strptime(
                            CONFIG["END"], "%Y-%m-%d"
                        ):
                            continue

                    name_soup = BeautifulSoup(row[1], "lxml")
                    link = name_soup.find("a")

                    data = {
                        "id": row[0],
                        "name": link.get_text(strip=True) if link else row[1],
                        "city": row[2],
                        "date": start_date,
                        "country": country,
                        "period": period,
                    }
                    out_file.write(json.dumps(data, ensure_ascii=False) + "\n")
                    count += 1

                logging.info(f"[{country}] {period}: {count} records")
                return count


async def main():
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}

    async with aiohttp.ClientSession(headers=headers) as session:
        scraper = FideScraper(session)
        countries = CONFIG["COUNTRIES"] or await scraper.fetch_countries()

        logging.info(f"Starting crawl for {len(countries)} countries")

        with open(CONFIG["FILE"], "w", encoding="utf-8") as f:
            # Busca períodos em paralelo
            period_tasks = [scraper.get_periods(c) for c in countries]
            all_periods = await asyncio.gather(*period_tasks)

            # Flat list de tarefas
            tasks = []
            for idx, country in enumerate(countries):
                for p in all_periods[idx]:
                    tasks.append(scraper.scrape_tournament_batch(country, p, f))

            results = await asyncio.gather(*tasks)
            logging.info(f"Finished. Total: {sum(results)} tournaments.")


if __name__ == "__main__":
    asyncio.run(main())
