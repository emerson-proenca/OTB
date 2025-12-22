import re

from bs4 import BeautifulSoup

from cbx_utils import get_asp_vars, get_session, get_supabase, save_data, setup_logging

logger = setup_logging()
supabase = get_supabase()
URL = "https://www.cbx.org.br/rating"
UF_ALVO = "SE"


def extract_page_data(soup: BeautifulSoup):
    """Extrai os dados da tabela de rating."""
    table = soup.find("table", id="ContentPlaceHolder1_gdvMain")
    if not table:
        return []

    data = []
    for row in table.find_all("tr"):
        cols = row.find_all("td")

        # Valida se é uma linha de jogador (mínimo 8 colunas e link de ID presente)
        if len(cols) >= 8:
            link_id = cols[0].find("a")
            if link_id and "/jogador/" in link_id.get("href", ""):
                data.append(
                    {
                        "cbx_id": link_id.text.strip(),
                        "nome": cols[1].text.strip(),
                        "nascimento": cols[2].text.strip(),
                        "uf": cols[3].text.strip(),
                        "fide_id": cols[4].text.strip(),
                        "classico": cols[5].text.strip(),
                        "rapido": cols[6].text.strip(),
                        "blitz": cols[7].text.strip(),
                    }
                )
    return data


def main():
    session = get_session()

    try:
        # 1. GET Inicial e Seleção de UF
        res = session.get(URL)
        soup = BeautifulSoup(res.text, "html.parser")

        payload = get_asp_vars(soup)
        payload.update(
            {
                "__EVENTTARGET": "ctl00$ContentPlaceHolder1$cboUF",
                "ctl00$ContentPlaceHolder1$cboUF": UF_ALVO,
            }
        )

        current_page = 1
        while True:
            logger.info(f"Processando página {current_page} para {UF_ALVO}...")
            res = session.post(URL, data=payload)
            soup = BeautifulSoup(res.text, "html.parser")

            # 2. Extração e Salvamento
            players = extract_page_data(soup)
            save_data(supabase, "cbx_jogadores", players, "cbx_id")

            # 3. Paginação
            next_page_num = current_page + 1
            if soup.find("a", href=re.compile(rf"Page\${next_page_num}")):
                payload = get_asp_vars(soup)
                payload.update(
                    {
                        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$gdvMain",
                        "__EVENTARGUMENT": f"Page${next_page_num}",
                        "ctl00$ContentPlaceHolder1$cboUF": UF_ALVO,
                    }
                )
                current_page += 1
            else:
                logger.info("Fim da lista alcançado.")
                break

    except Exception as e:
        logger.error(f"Erro durante a execução: {e}")


if __name__ == "__main__":
    main()
