# Configurações da API
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

class Settings:
    """Configurações da aplicação"""

    # Ambiente
    IS_RENDER = os.environ.get("RENDER") == "true"

    # Diretórios e Rede
    PORT = int(os.getenv("PORT", 8000))
    STATIC_DIR = "static"

    # BASE URL
    if os.getenv("BASE_URL"):
        BASE_URL = os.getenv("BASE_URL")
    elif os.getenv("CODESPACE_NAME") and os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN"):
        cname = os.getenv("CODESPACE_NAME")
        domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
        port = os.getenv("PORT", "8000")
        BASE_URL = f"https://{cname}-{port}.{domain}"
    else:
        BASE_URL = f"http://localhost:{PORT}"

    # API
    APP_NAME = "Over the Board"
    VERSION = "0.8.1"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # Cache
    CACHE_TTL_DEFAULT = int(os.getenv("CACHE_TTL_DEFAULT", "300"))  # 5 minutos
    CACHE_TTL_TOURNAMENTS = int(os.getenv("CACHE_TTL_TOURNAMENTS", "300"))
    CACHE_TTL_PLAYERS = int(os.getenv("CACHE_TTL_PLAYERS", "600"))  # 10 minutos
    CACHE_TTL_NEWS = int(os.getenv("CACHE_TTL_NEWS", "180"))  # 3 minutos

    # URLs da CBX
    CBX_BASE_URL = "https://www.cbx.org.br"
    CBX_TOURNAMENTS_URL = f"{CBX_BASE_URL}/torneios"
    CBX_PLAYERS_URL = f"{CBX_BASE_URL}/rating"
    CBX_NEWS_URL = f"{CBX_BASE_URL}/noticias"
    CBX_ANNOUNCEMENTS_URL = f"{CBX_BASE_URL}/comunicados"

    # Timeout para requisições HTTP
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "chess_api.log")

# Instância global das configurações
settings = Settings()
