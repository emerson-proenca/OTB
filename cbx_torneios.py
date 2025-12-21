import os
import re
import sys
import logging
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuração Supabase
load_dotenv()
url: str = os.environ['SUPABASE_URL']
key: str = os.environ['SUPABASE_SECRET_KEY']
supabase: Client = create_client(url, key)


def safe(element) -> str | None:
    if not element:
        return None
    match = re.search(r'.*?:\s*(.*)', element.text)
    if match:
        return match.group(1).strip() 
    else:
        return element.text.strip()


def extract_page_data(soup: BeautifulSoup, base_url: str):
    tables = soup.find_all('table', attrs={'class': 'torneios'})
    page_tournaments = []
    
    for i in range(len(tables)):
        def get_text(field):
            return safe(soup.find('span', id=re.compile(f'ContentPlaceHolder1_gdvMain_{field}_{i}')))
        
        reg_elem = soup.find('a', id=re.compile(f'ContentPlaceHolder1_gdvMain_hlkTorneio_{i}'))
        
        page_tournaments.append({
            'titulo': get_text('lblNomeTorneio'),
            'cbx_id': get_text('lblIDTorneio'),
            'organizador': get_text('lblOrganizador'),
            'local': get_text('lblLocal'),
            'periodo': get_text('lblPeriodo'),
            'observacao': get_text('lblObs'),
            'regulamento': (base_url + str(reg_elem.get('href'))) if (reg_elem and reg_elem.get('href')) else "",
            'situacao': get_text('lblStatus'),
            'ritmo': get_text('lblRitmo'),
            'rating': get_text('lblRating'),
            'jogadores': get_text('lblQtJogadores'),
            'jogadores_fide': get_text('lblQtJogadoresFIDE')
        })
    return page_tournaments


def save_to_supabase(data):
    if not data:
        return
    try:
        # Substitua 'torneios' pelo nome da sua tabela no Supabase
        response = supabase.table('cbx_torneios').upsert(data, on_conflict='cbx_id').execute()
        logger.info(f"Enviados {len(data)} registros para o Supabase.")
    except Exception as e:
        logger.error(f"Erro ao salvar no Supabase: {e}")


def main():
    URL = 'https://www.cbx.org.br/torneios'
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        logger.info("Iniciando conexão com CBX...")
        res = session.get(URL, headers=headers, timeout=30)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')

        def get_val(id_name):
            tag = soup.find('input', id=id_name)
            return tag.get('value', '') if tag else None
        
        year = '2025' 
        month = '' 

        payload = {
            '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$cboMes',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': get_val('__VIEWSTATE'),
            '__VIEWSTATEGENERATOR': get_val('__VIEWSTATEGENERATOR'),
            '__EVENTVALIDATION': get_val('__EVENTVALIDATION'),
            'ctl00$ContentPlaceHolder1$cboAno': year,
            'ctl00$ContentPlaceHolder1$cboMes': month
        }

        current_page = 1
        
        while True:
            logger.info(f"Processando página {current_page}...")
            res = session.post(URL, data=payload, headers=headers, timeout=30)
            res.raise_for_status()
            
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Extrai e já envia para o Supabase (Salva o progresso por página)
            tournaments = extract_page_data(soup, 'https://www.cbx.org.br/')
            save_to_supabase(tournaments)

            link_next = soup.find('a', href=re.compile(rf"Page\${current_page + 1}"))
            if link_next:
                current_page += 1
                payload.update({
                    '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$gdvMain',
                    '__EVENTARGUMENT': f'Page${current_page}',
                    '__VIEWSTATE': get_val('__VIEWSTATE'),
                    '__EVENTVALIDATION': get_val('__EVENTVALIDATION')
                })
            else:
                logger.info("Fim da paginação alcançado.")
                break
            
    except Exception as e:
        logger.critical(f"Erro inesperado: {str(e)}", exc_info=True)


if __name__ == '__main__':
    main()