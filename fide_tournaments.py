import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
from cbx_utils import setup_logging, get_supabase
import logging
import time
from typing import List, Dict, Any

# Configuração inicial
logging = setup_logging()
supabase = get_supabase()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://ratings.fide.com/rated_tournaments.phtml',
    'X-Requested-With': 'XMLHttpRequest'
}

class AsyncFIDEScraper:
    def __init__(self, max_concurrent=5):
        self.max_concurrent = max_concurrent
        self.session = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=HEADERS)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_html(self, url: str) -> str:
        """Busca conteúdo HTML/JSON de forma assíncrona"""
        async with self.semaphore:
            try:
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
            except Exception as e:
                logging.error(f"Erro ao buscar {url}: {e}")
                return ""
    
    async def fetch_all_country_codes(self) -> List[str]:
        """Extrai todos os códigos de países do dropdown"""
        url = "https://ratings.fide.com/rated_tournaments.phtml"
        html = await self.fetch_html(url)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        select_country = soup.find('select', {'id': 'select_country'})
        
        if not select_country:
            logging.error("Elemento select_country não encontrado")
            return []
        
        country_codes = [
            option['value'] for option in select_country.find_all('option')
            if option.get('value') and option['value'] != 'all'
        ]
        
        logging.info(f"Encontrados {len(country_codes)} códigos de país")
        return country_codes
    
    async def fetch_available_periods(self, country_code: str) -> List[str]:
        """Busca todos os períodos disponíveis para um país"""
        url = f"https://ratings.fide.com/a_tournaments_panel.php?country={country_code}&periods_tab=1"
        json_text = await self.fetch_html(url)
        
        if not json_text:
            return []
        
        try:
            periods_data = json.loads(json_text)
            periods = [item['frl_publish'] for item in periods_data]
            return periods
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"Erro ao processar períodos para {country_code}: {e}")
            return []
    
    async def fetch_tournaments_for_period(self, country_code: str, period: str) -> List[Dict[str, Any]]:
        """Busca torneios de um período específico"""
        timestamp = int(time.time() * 1000)
        url = f"https://ratings.fide.com/a_tournaments.php?country={country_code}&period={period}&_={timestamp}"
        
        json_text = await self.fetch_html(url)
        
        if not json_text:
            return []
        
        try:
            data = json.loads(json_text)
            tournaments = []
            
            for item in data.get('data', []):
                soup_name = BeautifulSoup(item[1], 'html.parser')
                soup_rcvd = BeautifulSoup(item[5], 'html.parser') if len(item) > 5 else None
                
                name_link = soup_name.find('a')
                name = name_link.get_text(strip=True) if name_link else item[1]
                link_event = name_link['href'] if name_link and 'href' in name_link.attrs else ''
                rcvd = soup_rcvd.find('a').get_text(strip=True) if soup_rcvd and soup_rcvd.find('a') else (item[5] if len(item) > 5 else '')
                
                tournament = {
                    'fide_id': item[0],
                    'link_information': f"https://ratings.fide.com/tournament_information.phtml?event={item[0]}",
                    'name': name,
                    'link_event': f"https://ratings.fide.com{link_event}" if link_event else '',
                    'city': item[2] if len(item) > 2 else '',
                    's': item[3] if len(item) > 3 else '',
                    'start': item[4] if len(item) > 4 else '',
                    'rcvd': rcvd,
                    'country': country_code,
                    'period': period
                }
                tournaments.append(tournament)
            
            logging.info(f"País {country_code}, período {period}: {len(tournaments)} torneios")
            return tournaments
            
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logging.error(f"Erro ao processar torneios para {country_code} ({period}): {e}")
            return []
    
    async def process_country(self, country_code: str) -> int:
        """Processa todos os períodos de um país"""
        periods = await self.fetch_available_periods(country_code)
        
        if not periods:
            logging.warning(f"Nenhum período encontrado para {country_code}")
            return 0
        
        total_tournaments = 0
        
        # Processar períodos em paralelo
        period_tasks = []
        for period in periods:
            task = asyncio.create_task(self.fetch_tournaments_for_period(country_code, period))
            period_tasks.append(task)
        
        # Coletar resultados de todos os períodos
        all_tournaments_results = await asyncio.gather(*period_tasks)
        
        # Consolidar torneios e fazer upsert
        for tournaments in all_tournaments_results:
            if tournaments:
                await self.upsert_tournaments(tournaments)
                total_tournaments += len(tournaments)
        
        return total_tournaments
    
    async def upsert_tournaments(self, tournaments: List[Dict[str, Any]]):
        """Faz upsert dos torneios no Supabase"""
        if not tournaments:
            return
        
        try:
            # Executar upsert em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: supabase.table('fide_tournaments').upsert(tournaments).execute()
            )
            logging.info(f"UPSERT realizado: {len(tournaments)} registros")
        except Exception as e:
            logging.error(f"Erro no UPSERT: {e}")
    
    async def run(self, test_mode=False, max_countries=None):
        """Executa o scraping completo"""
        start_time = time.time()
        
        async with self:
            # 1. Buscar todos os países
            logging.info("Buscando lista de países...")
            country_codes = await self.fetch_all_country_codes()
            
            if not country_codes:
                logging.error("Nenhum país encontrado")
                return
            
            # Modo teste: limitar países
            if test_mode:
                country_codes = country_codes[:5]
                logging.info(f"Modo teste: processando {len(country_codes)} países")
            elif max_countries:
                country_codes = country_codes[:max_countries]
                logging.info(f"Limitando a {max_countries} países")
            
            total_countries = len(country_codes)
            logging.info(f"Iniciando scraping para {total_countries} países")
            
            # 2. Processar países em paralelo com limitação de concorrência
            all_tasks = []
            for i, country_code in enumerate(country_codes, 1):
                logging.info(f"Agendando país {i}/{total_countries}: {country_code}")
                task = asyncio.create_task(self.process_country(country_code))
                all_tasks.append(task)
            
            # Aguardar conclusão de todos os países
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # 3. Resumo final
            total_tournaments = sum(r for r in results if isinstance(r, int))
            total_time = time.time() - start_time
            
            logging.info(f"SCRAPING CONCLUÍDO!")
            logging.info(f"Países processados: {total_countries}")
            logging.info(f"Torneios capturados: {total_tournaments}")
            logging.info(f"Tempo total: {total_time:.2f} segundos")
            logging.info(f"Tempo médio por país: {total_time/total_countries:.2f} segundos")

def main():
    """Função principal"""
    import sys
    
    # Configurar parâmetros
    test_mode = '--test' in sys.argv
    max_concurrent = 10  # Ajuste conforme necessário
    
    # Extrair número máximo de países se fornecido
    max_countries = None
    for arg in sys.argv:
        if arg.startswith('--countries='):
            try:
                max_countries = int(arg.split('=')[1])
            except ValueError:
                pass
    
    # Criar e executar scraper
    scraper = AsyncFIDEScraper(max_concurrent=max_concurrent)
    
    # Configurar asyncio para Windows se necessário
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Executar
    asyncio.run(scraper.run(test_mode=test_mode, max_countries=max_countries))

if __name__ == '__main__':
    main()