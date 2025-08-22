# Configurações da API
import os

class Settings:
    """Configurações da aplicação"""
    
    # Ambiente
    IS_RENDER = os.environ.get("RENDER") == "true"
    
    # Diretórios e Rede
    PORT = int(os.getenv("PORT", 3000))
    FRONTEND_DIR = "frontend"
    
    # BASE URL
    RENDER_URL = "https://over-the-board.onrender.com"
    LOCAL_URL = "http://localhost"
    BASE_URL = RENDER_URL if IS_RENDER else LOCAL_URL
    
    # API
    APP_NAME = "Over the Board"
    VERSION = "1.0.3"
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
