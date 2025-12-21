import os, re, sys, logging, requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv

# Configuração
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
supabase: Client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SECRET_KEY'])

URL = "https://www.cbx.org.br/rating"
UF_ALVO = 'SE' # Altere para a UF desejada

def extract_rating_data(soup):
    table = soup.find('table', id='ContentPlaceHolder1_gdvMain')
    if not table: return []
    
    rows = table.find_all('tr')
    data = []
    
    for row in rows:
        cols = row.find_all('td')
        
        # 1. Precisa ter pelo menos 8 colunas
        # 2. A primeira coluna DEVE conter um link (<a>) que é o ID do jogador
        if len(cols) >= 8:
            link_id = cols[0].find('a')
            if link_id and '/jogador/' in link_id.get('href', ''):
                data.append({
                    'cbx_id': link_id.text.strip(),
                    'nome': cols[1].text.strip(),
                    'nascimento': cols[2].text.strip(),
                    'uf': cols[3].text.strip(),
                    'fide_id': cols[4].text.strip(),
                    'classico': cols[5].text.strip(),
                    'rapido': cols[6].text.strip(),
                    'blitz': cols[7].text.strip()
                })
    return data

def save_to_supabase(data):
    if not data: return
    try:
        supabase.table('cbx_jogadores').upsert(data, on_conflict='cbx_id').execute()
        logger.info(f"Salvos {len(data)} jogadores.")
    except Exception as e:
        logger.error(f"Erro no Supabase: {e}")

def main():
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    # 1. GET Inicial
    res = session.get(URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    def get_asp_vars(s):
        return {
            '__VIEWSTATE': s.find('input', id='__VIEWSTATE')['value'],
            '__VIEWSTATEGENERATOR': s.find('input', id='__VIEWSTATEGENERATOR')['value'],
            '__EVENTVALIDATION': s.find('input', id='__EVENTVALIDATION')['value'],
        }

    # 2. Selecionar UF
    payload = get_asp_vars(soup)
    payload.update({
        '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$cboUF',
        'ctl00$ContentPlaceHolder1$cboUF': UF_ALVO
    })
    
    current_page = 1
    while True:
        logger.info(f"Processando página {current_page} para {UF_ALVO}...")
        res = session.post(URL, data=payload)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Extração e Save
        players = extract_rating_data(soup)
        if players:
            save_to_supabase(players)
        
        # 3. Paginação (Busca link para a próxima página)
        next_page_num = current_page + 1
        link_next = soup.find('a', href=re.compile(rf"Page\${next_page_num}"))
        
        if link_next:
            payload = get_asp_vars(soup)
            payload.update({
                '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$gdvMain',
                '__EVENTARGUMENT': f'Page${next_page_num}',
                'ctl00$ContentPlaceHolder1$cboUF': UF_ALVO
            })
            current_page += 1
        else:
            logger.info("Fim da lista alcançado.")
            break

if __name__ == '__main__':
    main()