import os
import logging
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_SECRET_KEY']
BASE_URL = 'https://ratings.fide.com/rated_tournaments.phtml'
API_URL = 'https://ratings.fide.com/a_tournaments.php'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': BASE_URL,
    'X-Requested-With': 'XMLHttpRequest'
}

logging.basicConfig(level=logging.INFO)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_periods():
    '''Extrai os períodos tentando capturar as opções do seletor.'''
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procura por todas as tags <option> dentro do select com id 'archive'
        select = soup.find('select', {'id': 'archive'})
        
        if select and select.find_all('option'):
            return [opt['value'] for opt in select.find_all('option') if opt.get('value')]
        
        # Caso o HTML venha vazio, definimos períodos padrão ou manuais 
        # (A FIDE frequentemente exige uma sessão ativa ou cookies para renderizar o seletor)
        logging.warning('Seletor vazio. Verificando renderização ou usando fallback.')
        return ['current', '2025-12-01', '2025-11-01', '2025-08-01'] 
        
    except Exception as e:
        logging.error(f'Erro ao obter períodos: {e}')
        return ['current']


def scrape_fide(country='all'):
    periods = get_periods()
    
    for period in periods:
        logging.info(f'Processando período: {period}')
        # O parâmetro 'period' é acoplado aqui na URL da API via params
        params = {'country': country, 'period': period}
        
        try:
            res = requests.get(API_URL, headers=HEADERS, params=params)
            raw_data = res.json().get('data', [])
            
            data_to_insert = [{
                # CORREÇÃO: f-string corrigida para acessar o índice do item
                'link': f'https://ratings.fide.com/report.phtml?event={item[0]}',
                'name': item[1],
                'city': item[2],
                's': item[3],
                'start': item[4],
                'rcvd': item[5]
            } for item in raw_data]

            if data_to_insert:
                supabase.table('fide_tournaments').upsert(data_to_insert).execute()
                logging.info(f'Inseridos {len(data_to_insert)} registros de {period}')
        except Exception as e:
            logging.error(f'Erro no período {period}: {e}')


if __name__ == '__main__':
    scrape_fide(country='ALB')