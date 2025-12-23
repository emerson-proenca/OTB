import re

from bs4 import BeautifulSoup

from src.scrapers.cbx.base_cbx import ScraperCbx


class ScraperCbxComunicados(ScraperCbx):
    def __init__(self, data_args=None, site_args=None, global_args=None):
        # Recebe argumentos específicos do dado (ex: year), do site e globais
        super().__init__(site_args, global_args)
        self.data_args = data_args or {}
        self.url = f"{self.base_domain}/comunicados"
        self.table_name = "cbx_comunicados"

    def _extract_page_data(self, soup: BeautifulSoup):
        """Extração pura dos dados da tabela."""
        page_notices = []
        rows = soup.find_all("tr")

        for row in rows:
            link_tag = row.find("a", id=re.compile(r"hlkTitulo"))
            date_tag = row.find("span", class_="date")

            if link_tag and date_tag:
                href = link_tag.get("href", "")
                full_link = (
                    self.base_domain.rstrip("/") + href
                    if href.startswith("/")
                    else href
                )

                page_notices.append(
                    {
                        "titulo": link_tag.get_text(strip=True),
                        "link": full_link,
                        "data_hora": date_tag.get_text(strip=True),
                    }
                )
        return page_notices

    def run(self):
        """Fluxo principal de execução."""
        try:
            self.logger.info("Iniciando extração de comunicados...")
            res = self.session.get(self.url, timeout=30)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")
            current_page = 1

            while current_page <= self.max_pages:
                self.logger.info(f"Processando página {current_page}...")

                notices = self._extract_page_data(soup)
                self.save(self.table_name, notices, pk="link")

                # Lógica de Paginação ASP.NET (Puxando vars da BaseCbx)
                next_page = current_page + 1
                next_page_link = soup.find("a", href=re.compile(rf"Page\${next_page}"))

                if next_page_link:
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
                    self.logger.info("Fim da paginação ou última página alcançada.")
                    break

        except Exception as e:
            self.logger.critical(f"Falha no scraper: {str(e)}", exc_info=True)
