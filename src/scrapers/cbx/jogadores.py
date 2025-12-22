import re

from bs4 import BeautifulSoup

from scrapers.cbx.base_cbx import ScraperCbx


class ScraperCbxJogadores(ScraperCbx):
    def __init__(self, data_args=None, site_args=None, global_args=None):
        super().__init__(site_args, global_args)
        self.data_args = data_args or {}
        self.url = f"{self.base_domain}/rating"
        self.table_name = "cbx_jogadores"

        # Lista completa para o caso de "*"
        self.todos_estados = [
            "AC",
            "AL",
            "AP",
            "AM",
            "BA",
            "CE",
            "DF",
            "ES",
            "GO",
            "MA",
            "MT",
            "MS",
            "MG",
            "PA",
            "PB",
            "PR",
            "PE",
            "PI",
            "RJ",
            "RN",
            "RS",
            "RO",
            "RR",
            "SC",
            "SP",
            "SE",
            "TO",
        ]

    def _extract_page_data(self, soup: BeautifulSoup) -> list[dict]:
        table = soup.find("table", id="ContentPlaceHolder1_gdvMain")
        if not table:
            return []

        data = []
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 8:
                link_id = cols[0].find("a")
                if link_id and "/jogador/" in link_id.get("href", ""):
                    data.append(
                        {
                            "cbx_id": link_id.get_text(strip=True),
                            "nome": cols[1].get_text(strip=True),
                            "nascimento": cols[2].get_text(strip=True),
                            "uf": cols[3].get_text(strip=True),
                            "fide_id": cols[4].get_text(strip=True),
                            "classico": cols[5].get_text(strip=True),
                            "rapido": cols[6].get_text(strip=True),
                            "blitz": cols[7].get_text(strip=True),
                        }
                    )
        return data

    def _scrape_state(self, uf: str):
        """Executa a lógica de paginação para um estado específico."""
        self.logger.info(f"Iniciando extração para o estado: {uf}")

        res = self.session.get(self.url)
        soup = BeautifulSoup(res.text, "html.parser")

        current_page = 1
        while current_page <= self.max_pages:
            self.logger.info(f"UF: {uf} | Página: {current_page}")

            # Payload para selecionar UF ou trocar página
            payload = self.get_asp_vars(soup)
            payload.update(
                {
                    "ctl00$ContentPlaceHolder1$cboUF": uf,
                    "__EVENTTARGET": "ctl00$ContentPlaceHolder1$gdvMain"
                    if current_page > 1
                    else "ctl00$ContentPlaceHolder1$cboUF",
                }
            )

            if current_page > 1:
                payload["__EVENTARGUMENT"] = f"Page${current_page}"

            res = self.session.post(self.url, data=payload)
            soup = BeautifulSoup(res.text, "html.parser")

            players = self._extract_page_data(soup)
            if not players:
                break

            self.save(self.table_name, players, pk="cbx_id")

            # Verifica se existe próxima página
            if soup.find("a", href=re.compile(rf"Page\${current_page + 1}")):
                current_page += 1
            else:
                break

    def run(self):
        # Validação de Argumentos
        state_input = self.data_args.get("state")

        if not state_input:
            raise ValueError("O argumento 'state' é obrigatório para CBX Jogadores.")

        # Define lista de execução
        ufs_para_rodar = self.todos_estados if state_input == "*" else [state_input]

        for uf in ufs_para_rodar:
            try:
                self._scrape_state(uf)
            except Exception as e:
                self.logger.error(f"Falha ao processar UF {uf}: {e}")
                continue
