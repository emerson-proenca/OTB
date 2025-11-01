from fastapi import APIRouter, HTTPException, Depends, Response, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Literal, Type
from db.session import SessionLocal
from db import models  # models.Member, models.Club, etc.
from core.config import settings

router = APIRouter(tags=["Auth"])
ph = PasswordHasher()

# JWT CONFIG
SECRET_KEY = settings.SECRET_KEY
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set! Check your .env file.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 365


# ------------------ SCHEMAS ------------------

class UserBase(BaseModel):
    email: EmailStr
    password: str
    type: Literal["member", "club"]  # permite expandir com novos tipos futuramente


class UserRegister(UserBase):
    username: str


class UserLogin(UserBase):
    pass


# ------------------ HELPER FUNCTIONS ------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_model_by_type(user_type: str) -> Type:
    """Retorna a classe de modelo SQLAlchemy correspondente ao tipo de usuário"""
    model_map = {
        "member": models.Member,
        "club": models.Club,
        # adicione outros tipos aqui futuramente (ex: "admin": models.Admin)
    }
    model_cls = model_map.get(user_type.lower())
    if not model_cls:
        raise HTTPException(status_code=400, detail=f"Invalid user type: {user_type}")
    return model_cls


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set! Check your .env file.")
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set! Check your .env file.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(request: Request, db: Session):
    """Identifica o usuário atual a partir do cookie JWT"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(token)
    user_id = payload.get("sub")
    user_type = payload.get("type")
    if not user_id or not user_type:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    model_cls = get_model_by_type(user_type)
    user = db.query(model_cls).filter(model_cls.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user, user_type


# ------------------ ROUTES ------------------

@router.post("/register", status_code=201)
async def register_user(data: UserRegister, response: Response, db: Session = Depends(get_db)):
    """Cria novo usuário (Member, Club, etc.) com base no 'type' informado"""
    Model = get_model_by_type(data.type)

    # valida duplicidade de email e username (se existir)
    if db.query(Model).filter(Model.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    if hasattr(Model, "username") and db.query(Model).filter(Model.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered.")

    hashed_password = ph.hash(data.password)

    # cria instância genérica
    new_user = Model(username=getattr(data, "username", None),
                     email=data.email,
                     password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id), "type": data.type})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # True em produção (HTTPS)
        samesite="lax",
        max_age=60 * 60 * 24 * 365,
    )
    return {"message": f"{data.type.capitalize()} created successfully"}


@router.post("/login")
async def login_user(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login genérico (Member, Club, etc.)"""
    Model = get_model_by_type(data.type)

    user = db.query(Model).filter(Model.email == data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    try:
        ph.verify(str(user.password), data.password)
    except argon2_exceptions.VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token({"sub": str(user.id), "type": data.type})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # True em produção
        samesite="lax",
        max_age=60 * 60 * 24 * 365,
    )
    return {"message": f"Login successful for {data.type}"}


@router.post("/logout")
async def logout_user(response: Response):
    """Remove o cookie JWT"""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(request: Request, db: Session = Depends(get_db)):
    """Obtém info do usuário logado"""
    user, user_type = get_current_user(request, db)
    base_info = {"id": user.id, "email": user.email, "type": user_type}
    if hasattr(user, "username"):
        base_info["username"] = user.username
    return base_info
