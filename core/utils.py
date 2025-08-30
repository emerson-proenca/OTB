from bs4 import BeautifulSoup
import re
from typing import Optional, Dict, Any
from core.logger_config import logger

def get_hidden_fields(soup):
    """Retorna os campos ASP.NET necessários para postback."""
    try:
        return {
            "__VIEWSTATE":          soup.find("input", {"name": "__VIEWSTATE"})["value"],
            "__VIEWSTATEGENERATOR": soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"],
            "__EVENTVALIDATION":    soup.find("input", {"name": "__EVENTVALIDATION"})["value"],
        }
    except (AttributeError, TypeError) as e:
        logger.error(f"Erro ao extrair campos hidden: {e}")
        return {}

def safe_find(parent, tag, **attrs):
    """Busca um elemento de forma segura, retornando string vazia se não encontrar"""
    try:
        elem = parent.find(tag, attrs=attrs)
        return elem.get_text(strip=True) if elem else ""
    except Exception as e:
        logger.warning(f"Erro em safe_find: {e}")
        return ""

def safe_link(parent, tag, attr_name, **attrs):
    """Extrai link de forma segura"""
    try:
        elem = parent.find(tag, attrs=attrs)
        return elem.get(attr_name, "").strip() if elem else ""
    except Exception as e:
        logger.warning(f"Erro em safe_link: {e}")
        return ""

def safe_line(parent, tag, **attrs):
    """Extrai texto com quebras de linha preservadas"""
    try:
        elem = parent.find(tag, attrs=attrs)
        if not elem:
            return ""
        for br in elem.find_all('br'):
            br.replace_with('\n')
        return elem.get_text().strip()
    except Exception as e:
        logger.warning(f"Erro em safe_line: {e}")
        return ""

def after_colon(text):
    """Extrai texto após os dois pontos"""
    if not text:
        return ""
    return text.partition(':')[-1].strip()

def clean_text(text: str) -> str:
    """Limpa texto removendo espaços extras e caracteres indesejados"""
    if not text:
        return ""
    
    # Remove espaços extras
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove caracteres de controle
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text

def extract_date(text: str) -> Optional[str]:
    """Extrai data de um texto usando regex"""
    if not text:
        return None
    
    # Padrões de data comuns
    patterns = [
        r'(\d{1,2}/\d{1,2}/\d{4})',  # dd/mm/yyyy
        r'(\d{1,2}-\d{1,2}-\d{4})',  # dd-mm-yyyy
        r'(\d{4}-\d{1,2}-\d{1,2})',  # yyyy-mm-dd
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

def validate_response_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Valida e limpa dados de resposta"""
    if not isinstance(data, dict):
        return {}
    
    cleaned_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            cleaned_data[key] = clean_text(value)
        elif isinstance(value, (int, float, bool)):
            cleaned_data[key] = value
        elif value is None:
            cleaned_data[key] = ""
        else:
            cleaned_data[key] = str(value)
    
    return cleaned_data

def format_tournament_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Formata dados de torneio para resposta padronizada"""
    return validate_response_data({
        "id": raw_data.get("ID", ""),
        "name": raw_data.get("name", ""),
        "status": raw_data.get("status", ""),
        "time_control": raw_data.get("time", ""),
        "rating": raw_data.get("rating", ""),
        "total_players": raw_data.get("total_players", ""),
        "fide_players": raw_data.get("fide_players", ""),
        "organizer": raw_data.get("organizer", ""),
        "location": raw_data.get("place", ""),
        "period": raw_data.get("period", ""),
        "observation": raw_data.get("observation", ""),
        "regulation_link": raw_data.get("regulation", ""),
        "page": raw_data.get("page", 1)
    })
