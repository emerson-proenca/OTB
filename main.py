# Importações do FastAPI
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Importações dos roteadores
from apis.tournaments_api import router as tournaments_router
from apis.status_api import router as status_router
from apis.players_api import router as players_router
from apis.announcements_api import router as announcements_router
from apis.news_api import router as news_router

# Importações de configuração e utilitários
from core.rate_limiter import rate_limit_middleware
from core.logger_config import logger
from core.cache import cache
from core.config import settings

# Configuração inicial do FastAPI
app = FastAPI(
    title="Over the Board",
    version="1.0.3",
    description="API for tournaments, players, news and announcements for all chess federations (In the future)",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(rate_limit_middleware)

# Montagem de arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# Registro de roteadores
app.include_router(tournaments_router)
app.include_router(players_router)
app.include_router(news_router)
app.include_router(announcements_router)
app.include_router(status_router)

# Endpoints principais
@app.get("/")
async def home_page(request: Request):
    """Página inicial da aplicação"""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return {"status": "healthy", "timestamp": "2025-08-01"}

# Endpoints de gerenciamento de cache
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

# Ponto de entrada da aplicação
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando Over the Board...")
    print("🚀 Iniciando Over the Board...")
    
    base_url = settings.BASE_URL
    
    print(f"🏠 Home: {base_url}/")
    print(f"📊 Docs: {base_url}/docs")
    print(f"📋 Redoc: {base_url}/redoc")
    print(f"🏥 Health: {base_url}/health")
    print(f"📊 Cache Status: {base_url}/cache/stats")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)