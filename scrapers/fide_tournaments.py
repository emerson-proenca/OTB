import asyncio
import time

from base import BaseScraper
from bs4 import BeautifulSoup

# URLs e Configurações específicas
BASE_URL = "https://ratings.fide.com/rated_tournaments.phtml"
PANEL_ENDPOINT = "https://ratings.fide.com/a_tournaments_panel.php"
DATA_ENDPOINT = "https://ratings.fide.com/a_tournaments.php"


class FideScraper(BaseScraper):
    def __init__(self, start_date="", end_date="", countries=None):
        super().__init__(db_name="tournaments.db", concurrent=10)
        self.start_date = start_date
        self.end_date = end_date
        self.countries = countries or []
        self.headers["Referer"] = BASE_URL

    def _get_text(self, html):
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        link = soup.find("a")
        return link.get_text(strip=True) if link else html

    async def get_country_codes(self, session):
        try:
            async with session.get(BASE_URL) as resp:
                soup = BeautifulSoup(await resp.text(), "html.parser")
                select = soup.find("select", {"id": "select_country"})
                if not select:
                    self.log.warning(" Element 'select_country' not found")
                    return []
                return [
                    opt["value"]
                    for opt in select.find_all("option")
                    if opt.get("value") and opt["value"] != "all"
                ]
        except Exception as e:
            self.log.error(f"Error fetching countries: {e}")
            return []

    async def get_periods(self, session, country_code):
        async with self.semaphore:
            try:
                params = {"country": country_code, "periods_tab": 1}
                async with session.get(PANEL_ENDPOINT, params=params) as resp:
                    data = await resp.json(content_type=None)
                    periods = [item["frl_publish"] for item in data]
                    self.log.info(f"{country_code} | {len(periods)} periods ")
                    return [item["frl_publish"] for item in data]
            except Exception as e:
                self.log.error(f"Fetching periods for {country_code}: {e}")
                return []

    async def fetch_tournaments(self, session, country_code, period):
        async with self.semaphore:
            params = {
                "country": country_code,
                "period": period,
                "_": int(time.time() * 1000),
            }
            try:
                async with session.get(DATA_ENDPOINT, params=params) as resp:
                    raw = await resp.json(content_type=None)
                    tournaments = []
                    for row in raw.get("data", []):
                        row = row + [None] * (6 - len(row))
                        if not self.is_within_range(
                            row[4], self.start_date, self.end_date
                        ):
                            continue

                        a_tag = BeautifulSoup(row[1], "html.parser").find("a")
                        tournaments.append(
                            {
                                "fide_id": int(row[0]),
                                "name": a_tag.get_text(strip=True) if a_tag else row[1],
                                "city": row[2],
                                "s": row[3],
                                "start": row[4],
                                "country": country_code,
                                "rcvd": self._get_text(row[5]),
                                "period": period,
                            }
                        )

                    self.save_to_db("tournaments", tournaments, pk="fide_id")
                    return len(tournaments)
            except Exception as e:
                self.log.error(f"Error in {country_code}/{period}: {e}")
                return 0

    async def scrape(self, session):
        target_countries = self.countries or await self.get_country_codes(session)
        self.log.info(f"Processing {len(target_countries)} countries")

        # Busca períodos
        period_tasks = [self.get_periods(session, code) for code in target_countries]
        periods_results = await asyncio.gather(*period_tasks)

        # Busca torneios
        tournament_tasks = []
        for i, code in enumerate(target_countries):
            for period in periods_results[i]:
                tournament_tasks.append(self.fetch_tournaments(session, code, period))

        results = await asyncio.gather(*tournament_tasks)
        self.log.info(
            f"Done! Total: {sum(results)} tournaments. DB Count: {self.db['tournaments'].count}"
        )


if __name__ == "__main__":
    scraper = FideScraper(start_date="", end_date="", countries=["AFG"])
    asyncio.run(scraper.run_scraper())
