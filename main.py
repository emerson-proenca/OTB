# Importa cada roteador da API 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tournaments_api import router as tournaments_router
from local.cbx.cbx_players import router as players_router
from local.cbx.cbx_news import router as news_router
from local.cbx.cbx_announcements import router as announcements_router
from rate_limiter import rate_limit_middleware
from logger_config import logger
from cache import cache
from config import settings

from fastapi.templating import Jinja2Templates
from fastapi import Request

# Informações básicas
app = FastAPI(
    title="Over the Board",
    version="1.0.3",
    description="API for tournaments, players, news and announcements for all chess federations (In the future)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração CORS para permitir acesso de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionar middleware de rate limiting
app.middleware("http")(rate_limit_middleware)

# Incluir todos os roteadores
app.include_router(tournaments_router)
app.include_router(players_router)
app.include_router(news_router)
app.include_router(announcements_router)

# @app.get("/", tags=["Root"])
# async def root():
#     """Página inicial da API com informações básicas"""
#     return {
#         "message": "Bem-vindo à Over the Board!",
#         "version": "1.0.3",
#         "description": "API para consulta de dados de xadrez da CBX",
#         "endpoints": {
#             "tournaments": "/tournaments - Lista torneios da CBX",
#             "players": "/jogadores - Lista jogadores por UF",
#             "news": "/noticias - Últimas notícias da CBX",
#             "announcements": "/comunicados - Comunicados oficiais",
#             "docs": "/docs - Documentação interativa",
#             "redoc": "/redoc - Documentação alternativa"
#         },
#         "author": "API não oficial da CBX",
#         "status": "online"
#     }

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

templates = Jinja2Templates(directory="frontend")

@app.get("/")
async def home_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )

@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return {"status": "healthy", "timestamp": "2025-08-01"}

@app.get("/cache/stats", tags=["Cache"])
async def cache_stats():
    """Retorna estatísticas do cache"""
    return {
        "cache_size": cache.size(),
        "description": "Número de itens atualmente em cache"
    }

@app.delete("/cache/clear", tags=["Cache"])
async def clear_cache():
    """Limpa todo o cache"""
    cache.clear()
    logger.info("Cache limpo manualmente")
    return {"message": "Cache limpo com sucesso"}

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Iniciando Over the Board...")
    print("🚀 Iniciando Over the Board...")
    if settings.IS_RENDER == True:
        print(f"📊 Documentação disponível em: {settings.RENDER_URL}/docs")
        print(f"📋 Redoc disponível em: {settings.RENDER_URL}/redoc")
        print(f"🏥 Health check em: {settings.RENDER_URL}/health")
        print(f"📊 Stats do cache em: {settings.RENDER_URL}/cache/stats")
    else:
        print(f"📊 Documentação disponível em: {settings.LOCAL_URL}:8000/docs")
        print(f"📋 Redoc disponível em: {settings.LOCAL_URL}:8000/redoc")
        print(f"🏥 Health check em: {settings.LOCAL_URL}:8000/health")
        print(f"📊 Stats do cache em: {settings.LOCAL_URL}:8000/cache/stats")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)