import re
from bs4 import BeautifulSoup
from cbx_utils import setup_logging, get_supabase, get_session, get_asp_vars, save_data


logger = setup_logging()
supabase = get_supabase()
URL = 'https://www.cbx.org.br/comunicados'
BASE_DOMAIN = 'https://www.cbx.org.br'


def extract_page_data(soup: BeautifulSoup):
    '''Extrai os comunicados da tabela da página atual.'''
    page_notices = []
    rows = soup.find_all('tr')
    
    for row in rows:
        link_tag = row.find('a', id=re.compile(r'hlkTitulo'))
        date_tag = row.find('span', class_='date')
        
        if link_tag and date_tag:
            href = link_tag.get('href', '')
            full_link = BASE_DOMAIN.rstrip('/') + href if href.startswith('/') else href
            
            page_notices.append({
                'titulo': link_tag.get_text(strip=True),
                'link': full_link,
                'data_hora': date_tag.get_text(strip=True)
            })
            
    return page_notices


def main():
    session = get_session()
    
    try:
        logger.info("Iniciando extração de comunicados...")
        res = session.get(URL, timeout=30)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        current_page = 1
        
        while True:
            logger.info(f"Processando página {current_page}...")
            
            # Extração e Salvamento
            notices = extract_page_data(soup)
            save_data(supabase, 'cbx_comunicados', notices, 'link')

            # Lógica de Paginação ASP.NET
            next_page = current_page + 1
            if soup.find('a', href=re.compile(rf"Page\${next_page}")):
                payload = get_asp_vars(soup)
                payload.update({
                    '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$gdvMain',
                    '__EVENTARGUMENT': f'Page${next_page}'
                })
                
                res = session.post(URL, data=payload, timeout=30)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, 'html.parser')
                current_page += 1
            else:
                logger.info("Fim da paginação.")
                break
            
    except Exception as e:
        logger.critical(f"Erro inesperado: {str(e)}", exc_info=True)


if __name__ == '__main__':
    main()