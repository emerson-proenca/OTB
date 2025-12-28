import asyncio
import json
import re

import aiohttp
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
OUTPUT_FILE = "cbx_noticias.jsonl"
CONCURRENT_REQUESTS = 5
NEWS_URL = "https://www.cbx.org.br/noticias"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_asp_vars(soup):
    return {
        n: soup.find("input", id=n).get("value", "")
        for n in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]
        if soup.find("input", id=n)
    }


def extract_news(soup):
    items = []
    for row in soup.find_all("tr"):
        link_tag = row.find("a", id=re.compile(r"hlkTitulo"))
        date_tag = row.find("span", class_="date")
        if link_tag and date_tag:
            # Extracts the ID from "/noticia/3961/title..."
            match = re.search(r"/noticia/(\d+)/", link_tag.get("href", ""))
            if match:
                items.append(
                    {
                        "news_id": int(match.group(1)),
                        "titulo": link_tag.get_text(strip=True),
                        "data_hora": date_tag.get_text(strip=True),
                    }
                )
    return items


async def fetch(session, semaphore, payload=None):
    async with semaphore:
        method = session.post if payload else session.get
        async with method(NEWS_URL, data=payload) as resp:
            return await resp.text()


async def main():
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        html = await fetch(session, semaphore)
        current_page = 1

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            while html:
                soup = BeautifulSoup(html, "html.parser")
                news = extract_news(soup)
                for item in news:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

                print(f"[SCRAPE] Page {current_page} | Found {len(news)}")

                next_page = current_page + 1
                if soup.find("a", href=re.compile(rf"Page\${next_page}")):
                    payload = get_asp_vars(soup)
                    payload.update(
                        {
                            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$gdvMain",
                            "__EVENTARGUMENT": f"Page${next_page}",
                        }
                    )
                    html = await fetch(session, semaphore, payload)
                    current_page += 1
                else:
                    break


if __name__ == "__main__":
    asyncio.run(main())
