import re

from bs4 import BeautifulSoup

from cbx_utils import (
    get_asp_vars,
    get_session,
    get_supabase,
    safe,
    save_data,
    setup_logging,
)

logger = setup_logging()
supabase = get_supabase()
URL = "https://www.cbx.org.br/torneios/"
BASE_URL = "https://www.cbx.org.br/"


def extract_page_data(soup: BeautifulSoup):
    """Extrai os dados de cada tabela de torneio na página."""
    tables = soup.find_all("table", attrs={"class": "torneios"})
    page_tournaments = []

    for i in range(len(tables)):

        def get_text(field):
            return safe(
                soup.find(
                    "span", id=re.compile(f"ContentPlaceHolder1_gdvMain_{field}_{i}")
                )
            )

        reg_elem = soup.find(
            "a", id=re.compile(f"ContentPlaceHolder1_gdvMain_hlkTorneio_{i}")
        )

        page_tournaments.append(
            {
                "titulo": get_text("lblNomeTorneio"),
                "cbx_id": get_text("lblIDTorneio"),
                "organizador": get_text("lblOrganizador"),
                "local": get_text("lblLocal"),
                "periodo": get_text("lblPeriodo"),
                "observacao": get_text("lblObs"),
                "regulamento": (BASE_URL + str(reg_elem.get("href")))
                if (reg_elem and reg_elem.get("href"))
                else "",
                "situacao": get_text("lblStatus"),
                "ritmo": get_text("lblRitmo"),
                "rating": get_text("lblRating"),
                "jogadores": get_text("lblQtJogadores"),
                "jogadores_fide": get_text("lblQtJogadoresFIDE"),
            }
        )
    return page_tournaments


def main():
    session = get_session()

    try:
        logger.info("Iniciando extração de torneios...")
        res = session.get(URL, timeout=30)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # Filtros iniciais
        year = "2025"
        month = ""
        payload = get_asp_vars(soup)
        payload.update(
            {
                "__EVENTTARGET": "ctl00$ContentPlaceHolder1$cboMes",
                "ctl00$ContentPlaceHolder1$cboAno": year,
                "ctl00$ContentPlaceHolder1$cboMes": month,
            }
        )

        current_page = 1
        while True:
            logger.info(f"Processando página {current_page}...")
            res = session.post(URL, data=payload, timeout=30)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            # Extração e Salvamento
            tournaments = extract_page_data(soup)
            save_data(supabase, "cbx_torneios", tournaments, "cbx_id")

            # Paginação
            next_page = current_page + 1
            if soup.find("a", href=re.compile(rf"Page\${next_page}")):
                payload = get_asp_vars(soup)
                payload.update(
                    {
                        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$gdvMain",
                        "__EVENTARGUMENT": f"Page${next_page}",
                        "ctl00$ContentPlaceHolder1$cboAno": year,
                        "ctl00$ContentPlaceHolder1$cboMes": month,
                    }
                )
                current_page += 1
            else:
                logger.info("Fim da paginação.")
                break

    except Exception as e:
        logger.critical(f"Erro inesperado: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
