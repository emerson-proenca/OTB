import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import json
import re
import logging
from http.server import BaseHTTPRequestHandler

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe(element) -> str:
    if not element: return ''
    match = re.search(r'.*?:\s*(.*)', element.text)
    return match.group(1).strip() if match else element.text.strip()

def extract_page_data(soup, base_url):
    tables = soup.find_all('table', attrs={'class': 'torneios'})
    page_tournaments = []
    for i in range(len(tables)):
        def get_text(field):
            return safe(soup.find('span', id=re.compile(f'ContentPlaceHolder1_gdvMain_{field}_{i}')))
        reg_elem = soup.find('a', id=re.compile(f'ContentPlaceHolder1_gdvMain_hlkTorneio_{i}'))
        page_tournaments.append({
            'titulo': get_text('lblNomeTorneio'),
            'id': get_text('lblIDTorneio'),
            'regulamento': (base_url + str(reg_elem.get('href'))) if (reg_elem and reg_elem.get('href')) else ""
            # ... adicione os outros campos aqui conforme seu código anterior
        })
    return page_tournaments

# O Vercel chama esta classe/método em requisições Python
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url_site = 'https://www.cbx.org.br/torneios'
        session = requests.Session()
        
        # Variáveis de filtro que você solicitou
        year = '2025' 
        month = ''    
        
        all_data = []
        
        try:
            res = session.get(url_site, timeout=20)
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
                'ctl00$ContentPlaceHolder1$cboAno': year,
                'ctl00$ContentPlaceHolder1$cboMes': month
            }

            # Loop de Paginação (Limitado para evitar timeout no Vercel)
            for page in range(1, 10): # Ajuste o limite conforme necessário
                res = session.post(url_site, data=payload, timeout=20)
                soup = BeautifulSoup(res.text, 'html.parser')
                all_data.extend(extract_page_data(soup, 'https://www.cbx.org.br/'))
                
                link_next = soup.find('a', href=re.compile(rf"Page\${page + 1}"))
                if not link_next: break
                
                payload.update({
                    '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$gdvMain',
                    '__EVENTARGUMENT': f'Page${page + 1}',
                    '__VIEWSTATE': get_val('__VIEWSTATE'),
                    '__EVENTVALIDATION': get_val('__EVENTVALIDATION')
                })

            # Resposta para o Vercel
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "count": len(all_data)}).encode())
            
            # Aqui você deve enviar all_data para um banco de dados, 
            # pois o sistema de arquivos do Vercel é somente leitura.
            
        except Exception as e:
            logger.error(f"Erro no Cron: {e}")
            self.send_response(500)
            self.end_headers()