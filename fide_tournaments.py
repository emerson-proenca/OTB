import json
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
START_DATE = ""  # "2000-01-01" or "" for no START_DATE filter
END_DATE = "2005-09-01"  # "2099-12-31" or "" for no END_DATE filter
COUNTRIES = ["BRA"]  # ["USA", "FRA"] or [] for all countries
OUTPUT_FILE = "tournaments.jsonl"

BASE_URL = "https://ratings.fide.com/rated_tournaments.phtml"
PANEL_ENDPOINT = "https://ratings.fide.com/a_tournaments_panel.php"
DATA_ENDPOINT = "https://ratings.fide.com/a_tournaments.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": BASE_URL,
    "X-Requested-With": "XMLHttpRequest",
}


def parse_date(date_str):
    """Safely parse YYYY-MM-DD strings."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def is_within_range(tournament_date_str, start_cfg, end_cfg):
    """Check if the tournament start date falls within the config range."""
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


def get_country_codes():
    """Extract all available country codes."""
    try:
        resp = requests.get(BASE_URL, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        select = soup.find("select", {"id": "select_country"})
        if not select:
            print("Warning: Element 'select_country' not found.")
            return []
        return [
            opt["value"]
            for opt in select.find_all("option")
            if opt.get("value") and opt["value"] != "all"
        ]
    except Exception as e:
        print(f"Error fetching countries: {e}")
        return []


def get_text(html):
    """Helper function to extract text from <a> tags or return pure HTML."""
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("a")
    return link.get_text(strip=True) if link else html


def get_periods(country_code):
    """Fetch available rating periods for a country."""
    try:
        resp = requests.get(
            PANEL_ENDPOINT,
            params={"country": country_code, "periods_tab": 1},
            headers=HEADERS,
        )
        return [item["frl_publish"] for item in resp.json()]
    except Exception as e:
        print(f"An exception occurred: {e}")
        return []


def fetch_tournaments(country_code, period):
    """Fetch and filter tournaments by date range."""
    params = {"country": country_code, "period": period, "_": int(time.time() * 1000)}
    try:
        resp = requests.get(DATA_ENDPOINT, params=params, headers=HEADERS)
        data = resp.json().get("data", [])
        tournaments = []

        for item in data:
            row = item + [None] * (6 - len(item))
            t_start_date = row[4]

            if not is_within_range(t_start_date, START_DATE, END_DATE):
                continue

            name_soup = BeautifulSoup(row[1], "html.parser")
            a_tag = name_soup.find("a")

            tournaments.append(
                {
                    "fide_id": row[0],
                    "name": a_tag.get_text(strip=True) if a_tag else row[1],
                    "city": row[2],
                    "s": row[3],
                    "start": t_start_date,
                    "country": country_code,
                    "rcvd": get_text(row[5]),
                    "period": period,
                    "link_information": f"https://ratings.fide.com/tournament_information.phtml?event={row[0]}",
                    "link_event": f"https://ratings.fide.com{a_tag['href']}"
                    if a_tag and "href" in a_tag.attrs
                    else None,
                }
            )
        return tournaments
    except Exception as e:
        print(f"Error in {country_code}/{period}: {e}")
        return []


def main():
    target_countries = COUNTRIES if COUNTRIES else get_country_codes()
    print(
        f"Targeting {len(target_countries)} countries. From {START_DATE or 'Any'} to {END_DATE or 'Any'}."
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for count, code in enumerate(target_countries, 1):
            periods = get_periods(code)
            print(f"[{count}/{len(target_countries)}] Processing {code}...")

            for period in periods:
                # time.sleep(0.5)  # Currently FIDE doesn't have Rate Limiting.
                results = fetch_tournaments(code, period)
                for t in results:
                    f.write(json.dumps(t, ensure_ascii=False) + "\n")

                if results:
                    print(f"  -> {period}: {len(results)} {code} tournaments saved.")

    print(f"Done! Results in {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
