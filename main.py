# Importar FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from whitenoise import WhiteNoise

# Importar routers
from apis.tournaments_api import router as tournaments_router
from apis.status_api import router as status_router
from apis.players_api import router as players_router
from apis.announcements_api import router as announcements_router
from apis.news_api import router as news_router

# Configs/utilitários
from core.rate_limiter import rate_limit_middleware
from core.logger_config import logger
from core.cache import cache
from core.config import settings

import os
from fastapi.responses import HTMLResponse

# Criar app FastAPI
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
app.add_middleware(GZipMiddleware, minimum_size=500)

# Arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers da API
app.include_router(tournaments_router)
app.include_router(players_router)
app.include_router(news_router)
app.include_router(announcements_router)
app.include_router(status_router)

# Endpoints principais
@app.get("/", response_class=HTMLResponse)
async def home_page():
    """Serve o index.html da pasta static"""
    with open(os.path.join("static", "index.html"), encoding="utf-8") as f:
        return f.read()

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "timestamp": "2025-08-01"}

@app.get("/cache/stats", tags=["Cache"])
async def cache_stats():
    return {"cache_size": cache.size(), "description": "Número de itens em cache"}

@app.delete("/cache/clear", tags=["Cache"])
async def clear_cache():
    cache.clear()
    logger.info("Cache limpo manualmente")
    return {"message": "Cache limpo com sucesso"}

# Conpressão de Dados
app.add_middleware(
    GZipMiddleware,
    minimum_size=500
)
app = WhiteNoise(app, root="static", prefix="static/")

# Entry point
if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Iniciando Over the Board...")

    base_url = settings.RENDER_URL if settings.IS_RENDER else f"{settings.LOCAL_URL}:8000"

    print(f"🏠 Home: {base_url}")
    print(f"📊 Docs: {base_url}/docs")
    print(f"📋 Redoc: {base_url}/redoc")
    print(f"🏥 Health: {base_url}/health")
    print(f"📊 Cache stats: {base_url}/cache/stats")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
