import re
from bs4 import BeautifulSoup
from cbx_utils import setup_logging, get_supabase, get_session, get_asp_vars, save_data

logger = setup_logging()
supabase = get_supabase()
URL = 'https://www.cbx.org.br/noticias'
BASE_URL = 'https://www.cbx.org.br/'


def extract_page_data(soup: BeautifulSoup):
    news_list = []
    for row in soup.find_all('tr'):
        link = row.find('a', id=re.compile(r'hlkTitulo'))
        date = row.find('span', class_='date')
        if link and date:
            news_list.append({
                'titulo': link.text.strip(),
                'link': BASE_URL + link.get('href').lstrip('/'),
                'data_hora': date.text.strip()
            })
    return news_list


def main():
    session = get_session()
    res = session.get(URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    current_page = 1

    while True:
        logger.info(f"Processando página {current_page}...")
        news = extract_page_data(soup)
        save_data(supabase, 'cbx_noticias', news, 'link')

        next_page = current_page + 1
        if soup.find('a', href=re.compile(rf"Page\${next_page}")):
            payload = get_asp_vars(soup)
            payload.update({
                '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$gdvMain',
                '__EVENTARGUMENT': f'Page${next_page}'
            })
            res = session.post(URL, data=payload)
            soup = BeautifulSoup(res.text, 'html.parser')
            current_page += 1
        else:
            break


if __name__ == '__main__':
    main()