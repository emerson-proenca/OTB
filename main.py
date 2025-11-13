# FastAPI and httpx imports
import httpx
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

# Router imports
from api.tournaments_api import router as tournaments_router
from api.member_api import router as member_router
from api.auth_api import router as auth_router
from api.club_api import router as club_router
from routes import club

# Configuration and utilities imports
from core.rate_limiter import rate_limit_middleware
from core.logger_config import logger
from core.cache import cache
from core.config import settings

# Db and models imports
from db.session import SessionLocal, engine
from db.models import Base, Member
from sqlalchemy.orm import Session

# JWT imports
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware

# JWT configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"


Base.metadata.create_all(bind=engine)

# FastAPI initial configuration
app = FastAPI(
    title="OTB",
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
# app.middleware("http")(rate_limit_middleware)

# Static files and templates setup
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(
    directory="templates",
    context_processors=[
        # Injects 'current_user' in ALL templates
        lambda request: {"current_user": request.state.current_user}
    ]
)


# Router registration
app.include_router(tournaments_router, prefix="/api")
app.include_router(member_router, prefix="/api")
app.include_router(club_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

app.include_router(club.router)


class CurrentUserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not SECRET_KEY:
            raise RuntimeError("SECRET_KEY is not set! Check your otb.env file.")
        token = request.cookies.get("access_token")
        request.state.current_user = None
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
                if user_id:
                    db = SessionLocal()
                    user = db.query(Member).filter(Member.id == user_id).first()
                    db.close()
                    if user:
                        request.state.current_user = user
            except JWTError:
                pass

        response = await call_next(request)
        return response

# Registrar o middleware
app.add_middleware(CurrentUserMiddleware)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# # Handler para 404 Not Found
# @app.exception_handler(StarletteHTTPException)
# async def http_exception_handler(request: Request, exc: StarletteHTTPException):
#     if exc.status_code == 404:
#         return templates.TemplateResponse(
#             "404.html", {"request": request}, status_code=404
#         )
#     return HTMLResponse(str(exc.detail), status_code=exc.status_code)


# # Handler para 500 Internal Server Error
# @app.exception_handler(Exception)
# async def internal_exception_handler(request: Request, exc: Exception):
#     print(f"Internal Server Error: {exc}")
#     return templates.TemplateResponse(
#         "500.html", {"request": request}, status_code=500
#     )


# WEBSITE PAGES
@app.get("/", response_class=HTMLResponse, name="home")
async def home_page(request: Request):
    """Site home page"""
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/create", response_class=HTMLResponse,)
async def create_form(request: Request):
    return templates.TemplateResponse("register_club.html", {"request": request})

@app.get("/login_club", response_class=HTMLResponse)
async def loginclub_form(request: Request):
    return templates.TemplateResponse("login_club.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse, name="admin")
async def admin_page(request: Request):
    """Site admin page"""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/about", response_class=HTMLResponse, name="about")
async def about_page(request: Request):
    """About page"""
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/tournaments", response_class=HTMLResponse, name="tournaments")
async def tournaments_page(request: Request):
    """Tournaments page using async httpx"""
    url = "http://localhost:8000/api/tournaments?limit=32"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        tournaments = response.json()
    
    return templates.TemplateResponse(
        "tournaments.html",
        {
            "request": request,
            "tournaments": tournaments
        }
    )

@app.get("/404", response_class=HTMLResponse, name="404",)
async def not_found(request: Request):
    """404 Not found"""
    return templates.TemplateResponse("404.html", {"request": request})

@app.get("/500", response_class=HTMLResponse, name="500",)
async def server_error(request: Request):
    """500 Internal Server Error"""
    return templates.TemplateResponse("500.html", {"request": request})
  
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


@app.get("/@/{username}/", response_class=HTMLResponse)
async def member_profile(
    request: Request,
    username: str,
    db: Session = Depends(get_db),
):
    """Página de perfil de uma pessoa (ex: /@/emerson/)."""
    user = db.query(Member).filter(Member.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
        },
    )


# Application entry point
if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting OTB...")
    
    base_url = settings.BASE_URL
    
    logger.info(f"🏠 Home: {base_url}/")
    logger.info(f"📊 Docs: {base_url}/docs")
    logger.info(f"📋 Redoc: {base_url}/redoc")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, proxy_headers=True)