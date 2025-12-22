import re

from scrapers.base import BaseScraper


class ScraperCbx(BaseScraper):
    def __init__(self, site_args=None, global_args=None):
        # Mescla argumentos globais com os específicos do site
        super().__init__(global_args)
        self.site_args = site_args or {}
        self.base_domain = "https://www.cbx.org.br"

    def get_asp_vars(self, soup):
        """Lógica ASP.NET centralizada para qualquer scraper da CBX."""

        def extract(id_name):
            tag = soup.find("input", id=id_name)
            return tag.get("value", "") if tag else None

        return {
            "__VIEWSTATE": extract("__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": extract("__VIEWSTATEGENERATOR"),
            "__EVENTVALIDATION": extract("__EVENTVALIDATION"),
        }

    def clean_text(self, element):
        """O seu 'safe()' agora como método da CBX."""
        if not element:
            return None
        match = re.search(r".*?:\s*(.*)", element.text)
        return match.group(1).strip() if match else element.text.strip()
