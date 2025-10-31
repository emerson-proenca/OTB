from fastapi import APIRouter, HTTPException, Depends, Response, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from db.session import SessionLocal
from db.models import Member
from core.config import settings

router = APIRouter(tags=["Auth"])
ph = PasswordHasher()

# JWT Configuration
SECRET_KEY = settings.SECRET_KEY
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set! Check your otb.env file.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 365

# ------------------ HELPER FUNCTION ------------------

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ------------------ HELPER FUNCTION ------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set! Check your otb.env file.")

    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(request: Request, db: Session):
    """Reads JWT cookie and returns the current user"""
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set! Check your otb.env file.")

    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = int(user_id_str)

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(Member).filter(Member.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ------------------ ROUTER ------------------

@router.post("/register", status_code=201)
async def register_user(user: UserCreate, response: Response, db: Session = Depends(get_db)):
    """Creates new user and logins in by setting JWT cookie"""

    if db.query(Member).filter(Member.email == user.email).first():
        raise HTTPException(status_code=400, detail="email already registered.")
    if db.query(Member).filter(Member.username == user.username).first():
        raise HTTPException(status_code=400, detail="username already registered.")

    hashed_password = ph.hash(user.password)

    new_user = Member(username=user.username, email=user.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # GENERATES JWT TOKEN AND SETS COOKIE
    token = create_access_token({"sub": str(new_user.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # SWITCH TO TRUE IN PRODUCTION WITH HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 365,  # 1 YEAR
    )
    return {"message": "User created successfully"}


@router.post("/login")
async def login_user(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login and set JWT cookie"""

    member = db.query(Member).filter(Member.email == user.email).first()
    if not member:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    try:
        ph.verify(str(member.password), user.password)
    except argon2_exceptions.VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token({"sub": str(member.id)})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # TRUE IN PRODUCTION WITH HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 365,
    )
    return {"message": "Login successful"}


@router.get("/me")
async def get_me(request: Request, db: Session = Depends(get_db)):
    """Obtains current logged in user info"""
    user = get_current_user(request, db)
    return {"id": user.id, "username": user.username, "email": user.email}


@router.post("/logout")
async def logout_user(response: Response):
    """Deletes the JWT cookie to logout the user"""
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}
