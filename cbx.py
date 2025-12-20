import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import json
import re

def safe(element) -> str:
    if not element: return ''
    match = re.search(r'.*?:\s*(.*)', element.text)
    return match.group(1).strip() if match else element.text.strip()

def extract_page_data(soup: BeautifulSoup, base_url: str):
    tables = soup.find_all('table', attrs={'class': 'torneios'})
    page_tournaments = []
    for i in range(len(tables)):
        def get_text(field):
            return safe(soup.find('span', id=re.compile(f'ContentPlaceHolder1_gdvMain_{field}_{i}')))
        reg_elem = soup.find('a', id=re.compile(f'ContentPlaceHolder1_gdvMain_hlkTorneio_{i}'))
        page_tournaments.append({
            'titulo': get_text('lblNomeTorneio'),
            'id': get_text('lblIDTorneio'),
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

def main():
    URL = 'https://www.cbx.org.br/torneios'
    session = requests.Session()
    
    # Configura retentativas automáticas (3 vezes antes de desistir)
    retry_strategy = Retry(
        total=3,
        backoff_factor=1, # Espera 1s, 2s, 4s entre tentativas
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        # Timeout de 30 segundos para evitar travar o CronJob
        res = session.get(URL, headers=headers, timeout=30)
        soup = BeautifulSoup(res.text, 'html.parser')

        def get_val(id_name):
            tag = soup.find('input', id=id_name)
            return tag.get('value', '') if tag else ''

        payload = {
            '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$cboMes',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': get_val('__VIEWSTATE'),
            '__VIEWSTATEGENERATOR': get_val('__VIEWSTATEGENERATOR'),
            '__EVENTVALIDATION': get_val('__EVENTVALIDATION'),
            'ctl00$ContentPlaceHolder1$cboAno': '2025',
            'ctl00$ContentPlaceHolder1$cboMes': ''
        }

        all_tournaments = []
        current_page = 1
        
        while True:
            res = session.post(URL, data=payload, headers=headers, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            print(f"Página {current_page} extraída.")
            all_tournaments.extend(extract_page_data(soup, 'https://www.cbx.org.br/'))

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
                break

        with open('torneios.json', 'w', encoding='utf-8') as f:
            json.dump(all_tournaments, f, indent=4, ensure_ascii=False)
            
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")

if __name__ == '__main__':
    main()