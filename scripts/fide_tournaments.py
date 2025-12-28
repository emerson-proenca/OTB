import asyncio
import json
import time
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
START_DATE = ""  # "2000-01-01" or "" for no START_DATE filter
END_DATE = ""  # "2099-12-31" or "" for no END_DATE filter
COUNTRIES = []  # ["USA", "FRA"] or [] for all countries
OUTPUT_FILE = "aaa.jsonl"
CONCURRENT_REQUESTS = 10

BASE_URL = "https://ratings.fide.com/rated_tournaments.phtml"
PANEL_ENDPOINT = "https://ratings.fide.com/a_tournaments_panel.php"
DATA_ENDPOINT = "https://ratings.fide.com/a_tournaments.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": BASE_URL,
    "X-Requested-With": "XMLHttpRequest",
}


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def is_within_range(tournament_date_str, start_cfg, end_cfg):
    if not tournament_date_str or tournament_date_str == "0000-00-00":
        return True
    t_date = parse_date(tournament_date_str)
    if not t_date:
        return True
    start_limit = parse_date(start_cfg)
    end_limit = parse_date(end_cfg)
    if start_limit and t_date < start_limit:
        return False
    if end_limit and t_date > end_limit:
        return False
    return True


def get_text(html):
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("a")
    return link.get_text(strip=True) if link else html


async def get_country_codes(session):
    try:
        async with session.get(BASE_URL) as resp:
            text = await resp.text()
            soup = BeautifulSoup(text, "html.parser")
            select = soup.find("select", {"id": "select_country"})
            if not select:
                print("[WARN] Element 'select_country' not found")
                return []
            return [
                opt["value"]
                for opt in select.find_all("option")
                if opt.get("value") and opt["value"] != "all"
            ]
    except Exception as e:
        print(f"[ERROR] Fetching countries: {e}")
        return []


async def get_periods(session, country_code, semaphore):
    async with semaphore:
        try:
            params = {"country": country_code, "periods_tab": 1}
            async with session.get(PANEL_ENDPOINT, params=params) as resp:
                data = await resp.json(content_type=None)
                periods = [item["frl_publish"] for item in data]
                print(f"[INFO  ] {country_code} | {len(periods)} periods")
                return periods
        except Exception as e:
            print(f"[ERROR] Fetching periods for {country_code}: {e}")
            return []


async def fetch_tournaments(session, country_code, period, semaphore, file_handle):
    async with semaphore:
        params = {
            "country": country_code,
            "period": period,
            "_": int(time.time() * 1000),
        }
        try:
            print(f"[SCRAPE] {country_code} | {period}")
            async with session.get(DATA_ENDPOINT, params=params) as resp:
                raw_data = await resp.json(content_type=None)
                data = raw_data.get("data", [])
                count = 0
                for item in data:
                    row = item + [None] * (6 - len(item))
                    t_start_date = row[4]

                    if not is_within_range(t_start_date, START_DATE, END_DATE):
                        continue

                    name_soup = BeautifulSoup(row[1], "html.parser")
                    a_tag = name_soup.find("a")

                    t = {
                        "fide_id": int(row[0]),
                        "name": a_tag.get_text(strip=True) if a_tag else row[1],
                        "city": row[2],
                        "s": row[3],
                        "start": t_start_date,
                        "country": country_code,
                        "rcvd": get_text(row[5]),
                        "period": period,
                    }
                    file_handle.write(json.dumps(t, ensure_ascii=False) + "\n")
                    count += 1
                print(f"[SAVE  ] {country_code} | {period} | {count} tournaments")
                return count
        except Exception as e:
            print(f"[ERROR] In {country_code} for {period}: {e}")
            return 0


async def main():
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        target_countries = COUNTRIES if COUNTRIES else await get_country_codes(session)
        print(f"[INFO  ] Found {len(target_countries)} countries")

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            period_tasks = [
                get_periods(session, code, semaphore) for code in target_countries
            ]
            all_periods_results = await asyncio.gather(*period_tasks)

            tournament_tasks = []
            for i, code in enumerate(target_countries):
                for period in all_periods_results[i]:
                    tournament_tasks.append(
                        fetch_tournaments(session, code, period, semaphore, f)
                    )

            print(f"[INFO  ] Fetching {len(tournament_tasks)} tournaments\n")
            results = await asyncio.gather(*tournament_tasks)
            print(f"\n[INFO  ] Done! Saved {sum(results)} tournaments to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
