import re

from bs4 import BeautifulSoup

from src.scrapers.cbx.base_cbx import ScraperCbx


class ScraperCbxTorneios(ScraperCbx):
    def __init__(self, data_args=None, site_args=None, global_args=None):
        super().__init__(site_args, global_args)
        self.data_args = data_args or {}
        self.url = f"{self.base_domain}/torneios/"
        self.table_name = "cbx_torneios"

        # Configurações de domínio da CBX
        self.anos_disponiveis = [str(ano) for ano in range(2005, 2026)]
        self.meses_disponiveis = [str(mes) for mes in range(1, 13)]

    def _extract_page_data(self, soup: BeautifulSoup) -> list[dict]:
        """Extrai os dados de cada tabela de torneio na página."""
        tables = soup.find_all("table", attrs={"class": "torneios"})
        page_tournaments = []

        for i in range(len(tables)):

            def get_field(field_name):
                # Usa o clean_text herdado da ScraperCbx (o antigo safe)
                elem = soup.find(
                    "span",
                    id=re.compile(f"ContentPlaceHolder1_gdvMain_{field_name}_{i}"),
                )
                return self.clean_text(elem)

            reg_elem = soup.find(
                "a", id=re.compile(f"ContentPlaceHolder1_gdvMain_hlkTorneio_{i}")
            )

            page_tournaments.append(
                {
                    "titulo": get_field("lblNomeTorneio"),
                    "cbx_id": get_field("lblIDTorneio"),
                    "organizador": get_field("lblOrganizador"),
                    "local": get_field("lblLocal"),
                    "periodo": get_field("lblPeriodo"),
                    "observacao": get_field("lblObs"),
                    "regulamento": f"{self.base_domain}/{reg_elem.get('href').lstrip('/')}"
                    if reg_elem and reg_elem.get("href")
                    else None,
                    "situacao": get_field("lblStatus"),
                    "ritmo": get_field("lblRitmo"),
                    "rating": get_field("lblRating"),
                    "jogadores": get_field("lblQtJogadores"),
                    "jogadores_fide": get_field("lblQtJogadoresFIDE"),
                }
            )
        return page_tournaments

    def _scrape_periodo(self, year: str, month: str):
        """Executa a paginação para um par específico de Ano/Mês."""
        self.logger.info(f"Extraindo: {month}/{year}")

        res = self.session.get(self.url)
        soup = BeautifulSoup(res.text, "html.parser")

        current_page = 1
        while current_page <= self.max_pages:
            self.logger.info(f"Ano: {year} | Mês: {month} | Página: {current_page}")

            payload = self.get_asp_vars(soup)
            payload.update(
                {
                    "ctl00$ContentPlaceHolder1$cboAno": year,
                    "ctl00$ContentPlaceHolder1$cboMes": month,
                    "__EVENTTARGET": "ctl00$ContentPlaceHolder1$gdvMain"
                    if current_page > 1
                    else "ctl00$ContentPlaceHolder1$cboMes",
                }
            )

            if current_page > 1:
                payload["__EVENTARGUMENT"] = f"Page${current_page}"

            res = self.session.post(self.url, data=payload, timeout=30)
            soup = BeautifulSoup(res.text, "html.parser")

            tournaments = self._extract_page_data(soup)
            if not tournaments:
                break

            self.save(self.table_name, tournaments, pk="cbx_id")

            if soup.find("a", href=re.compile(rf"Page\${current_page + 1}")):
                current_page += 1
            else:
                break

    def run(self):
        year_input = self.data_args.get("year")
        month_input = self.data_args.get("month")

        # Regra: Ano e Mês são obrigatórios (não podem ser None ou vazios)
        if not year_input or not month_input:
            raise ValueError(
                "Argumentos 'year' e 'month' são obrigatórios para Torneios da CBX."
            )

        # Lógica de Wildcard "*"
        anos = self.anos_disponiveis if year_input == "*" else [year_input]
        meses = self.meses_disponiveis if month_input == "*" else [month_input]

        for ano in anos:
            for mes in meses:
                try:
                    self._scrape_periodo(ano, mes)
                except Exception as e:
                    self.logger.error(f"Erro em {mes}/{ano}: {e}")
                    continue
