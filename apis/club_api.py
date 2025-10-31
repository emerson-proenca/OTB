from fastapi import APIRouter, HTTPException, status, Depends, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from db.session import SessionLocal
from db.models import Club, Member
from jose import jwt
from datetime import datetime, timedelta
from core.config import settings

router = APIRouter(tags=["Club"])
ph = PasswordHasher()

SECRET_KEY = settings.SECRET_KEY
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set! Check your otb.env file.")

ALGORITHM = "HS256"


class ClubCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    owner_id: int

class ClubLogin(BaseModel):
    email: EmailStr
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/club/register", status_code=status.HTTP_201_CREATED)
async def register_club(club: ClubCreate, response: Response, db: Session = Depends(get_db)):
    """Cria uma nova conta de c (precisa de owner_id válido)"""
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set! Check your otb.env file.")

    # Verifica se o owner existe
    owner = db.query(Member).filter(Member.id == club.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found.")

    # Verifica duplicatas
    if db.query(Club).filter(Club.email == club.email).first():
        raise HTTPException(status_code=400, detail="Club email already registered.")

    if db.query(Club).filter(Club.name == club.name).first():
        raise HTTPException(status_code=400, detail="Club name already taken.")

    # Criptografa senha
    hashed_pwd = ph.hash(club.password)

    # Cria club
    new_club = Club(
        name=club.name,
        email=club.email,
        password=hashed_pwd,
        owner_id=club.owner_id
    )
    db.add(new_club)
    db.commit()
    db.refresh(new_club)

    # Gera JWT
    exp = datetime.utcnow() + timedelta(days=365)
    payload = {
        "id": new_club.id,
        "role": "club",
        "exp": exp
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    response.set_cookie(
        key="club_jwt",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=365 * 24 * 60 * 60
    )

    return {"message": "Club account created successfully."}




@router.post("/club/login")
async def login_club(club: ClubLogin, response: Response, db: Session = Depends(get_db)):
    """Login da conta de Clube"""
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set! Check your otb.env file.")

    club = db.query(Club).filter(Club.email == club.email).first()

    if not club:
        raise HTTPException(status_code=400, detail="Invalid email or password.")

    try:
        ph.verify(str(club.password), str(club.password))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid email or password.")

    exp = datetime.utcnow() + timedelta(days=365)
    token = jwt.encode({"club_id": club.id, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

    # Gera JWT
    exp = datetime.utcnow() + timedelta(days=365)
    payload = {
        "id": club.id,
        "role": "club",
        "exp": exp
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


    response.set_cookie(
        key="club_jwt",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=365 * 24 * 60 * 60
    )

    return {"message": "Club login successful."}


@router.post("/club/logout")
async def logout_club(response: Response):
    """Logout da conta de clube"""

    response.delete_cookie("club_jwt")
    return {"message": "Club logged out successfully."}

