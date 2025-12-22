import re

from bs4 import BeautifulSoup

from scrapers.cbx.base_cbx import ScraperCbx


class ScraperCbxNoticias(ScraperCbx):
    def __init__(self, data_args=None, site_args=None, global_args=None):
        super().__init__(site_args, global_args)
        # Argumentos específicos para notícias (caso queira expandir no futuro)
        self.data_args = data_args or {}
        self.url = f"{self.base_domain}/noticias"
        self.table_name = "cbx_noticias"

    def _extract_page_data(self, soup: BeautifulSoup) -> list[dict]:
        """Extrai as notícias da tabela da página atual."""
        news_list = []
        for row in soup.find_all("tr"):
            link_tag = row.find("a", id=re.compile(r"hlkTitulo"))
            date_tag = row.find("span", class_="date")

            if link_tag and date_tag:
                href = link_tag.get("href", "").lstrip("/")
                news_list.append(
                    {
                        "titulo": link_tag.get_text(strip=True),
                        "link": f"{self.base_domain}/{href}",
                        "data_hora": date_tag.get_text(strip=True),
                    }
                )
        return news_list

    def run(self):
        """Fluxo principal de execução com suporte a max_pages."""
        try:
            self.logger.info("Iniciando extração de notícias...")
            res = self.session.get(self.url, timeout=30)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")
            current_page = 1

            while current_page <= self.max_pages:
                self.logger.info(f"Processando página {current_page}...")

                news = self._extract_page_data(soup)
                # O método save() já está na BaseScraper
                self.save(self.table_name, news, pk="link")

                # Lógica de Paginação ASP.NET (Puxando get_asp_vars da BaseCbx)
                next_page = current_page + 1
                if soup.find("a", href=re.compile(rf"Page\${next_page}")):
                    payload = self.get_asp_vars(soup)
                    payload.update(
                        {
                            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$gdvMain",
                            "__EVENTARGUMENT": f"Page${next_page}",
                        }
                    )

                    res = self.session.post(self.url, data=payload, timeout=30)
                    res.raise_for_status()
                    soup = BeautifulSoup(res.text, "html.parser")
                    current_page += 1
                else:
                    self.logger.info("Fim da paginação.")
                    break

        except Exception as e:
            self.logger.critical(f"Erro no scraper de notícias: {e}", exc_info=True)
