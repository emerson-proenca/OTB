import asyncio
import logging
from datetime import datetime

import aiohttp
import sqlite_utils


class BaseScraper:
    def __init__(self, db_name="data.db", concurrent=10):
        # CONFIGS
        self.db = sqlite_utils.Database(db_name)
        self.semaphore = asyncio.Semaphore(concurrent)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
        self.log = logging.getLogger(__name__)

    # UTILS
    def parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    def is_within_range(self, t_date_str, start_cfg, end_cfg):
        if not t_date_str or t_date_str == "0000-00-00":
            return True
        t_date = self.parse_date(t_date_str)
        if not t_date:
            return True

        start_limit = self.parse_date(start_cfg)
        end_limit = self.parse_date(end_cfg)

        if start_limit and t_date < start_limit:
            return False
        if end_limit and t_date > end_limit:
            return False
        return True

    # SAVING
    def save_to_db(self, table_name, data, pk="id"):
        if not data:
            return

        table = self.db[table_name]
        before_count = table.count if table.exists() else 0

        table.upsert_all(data, pk=pk)  # type: ignore

        after_count = table.count
        inserted = after_count - before_count
        updated = len(data) - inserted

        if inserted > 0:
            self.log.info(f"Inserted | {inserted} items in {table_name}")
        if updated > 0:
            self.log.info(f"Updated  | {updated} items in {table_name}")

    # ASYNC
    async def run_scraper(self):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            await self.scrape(session)

    async def scrape(self, session):
        raise NotImplementedError("Subclasses must implement scrape()")
