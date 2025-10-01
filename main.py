# FastAPI imports
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Router imports
from apis.tournaments_api import router as tournaments_router
from apis.status_api import router as status_router
from apis.players_api import router as players_router
from apis.announcements_api import router as announcements_router
from apis.news_api import router as news_router

# Configuration and utilities imports
from core.rate_limiter import rate_limit_middleware
from core.logger_config import logger
from core.cache import cache
from core.config import settings

# FastAPI initial configuration
app = FastAPI(
    title="Over the Board",
    version="0.8.1",
    description="Your platform for finding and registering for live chess tournaments",
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

# Static files and templates setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Router registration
app.include_router(tournaments_router, prefix="/api")
app.include_router(players_router, prefix="/api")
app.include_router(news_router, prefix="/api")
app.include_router(announcements_router, prefix="/api")
app.include_router(status_router, prefix="/api")


# WEBSITE PAGES
@app.get("/", response_class=HTMLResponse, name="home",)
async def home_page(request: Request):
    """Application home page"""
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse, name="admin")
async def admin_page(request: Request):
    """Site admin page"""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/about", response_class=HTMLResponse, name="about")
async def about_page(request: Request):
    """About page"""
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/announcements", response_class=HTMLResponse, name="announcements")
async def announcements_page(request: Request):
    """Announcements page"""
    return templates.TemplateResponse("announcements.html", {"request": request})

@app.get("/news", response_class=HTMLResponse, name="news")
async def news_page(request: Request):
    """News page"""
    return templates.TemplateResponse("news.html", {"request": request})

@app.get("/tournaments", response_class=HTMLResponse, name="tournaments")
async def tournaments_page(request: Request):
    """Tournaments page"""
    return templates.TemplateResponse("tournaments.html", {"request": request})

@app.get("/players", response_class=HTMLResponse, name="players")
async def players_page(request: Request):
    """Players page"""
    return templates.TemplateResponse("players.html", {"request": request})

  
# HEALTH AND CACHE ENDPOINTS
@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint to check if the API is running"""
    return {"status": "healthy", "timestamp": "2025-08-01"}

@app.get("/cache/stats", tags=["Cache"])
async def cache_stats():
    """Returns cache statistics"""
    return {
        "cache_size": cache.size(),
        "description": "Number of items currently in cache"
    }

@app.delete("/cache/clear", tags=["Cache"])
async def clear_cache():
    """Clears all cache"""
    cache.clear()
    logger.info("Cache cleared manually")
    return {"message": "Cache cleared successfully"}


# Application entry point
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Over the Board...")
    
    base_url = settings.BASE_URL
    
    logger.info(f"🏠 Home: {base_url}/")
    logger.info(f"📊 Docs: {base_url}/docs")
    logger.info(f"📋 Redoc: {base_url}/redoc")
    logger.info(f"🏥 Health: {base_url}/health")
    logger.info(f"📊 Cache Status: {base_url}/cache/stats")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)