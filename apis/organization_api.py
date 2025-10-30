from fastapi import APIRouter, HTTPException, status, Depends, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from database.session import SessionLocal
from database.models import Organization, People
from jose import jwt
from datetime import datetime, timedelta
from core.config import settings
import os

router = APIRouter(tags=["Organization"])
ph = PasswordHasher()

SECRET_KEY = settings.SECRET_KEY
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set! Check your otb.env file.")

ALGORITHM = "HS256"


class OrgCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    owner_id: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/organization/register", status_code=status.HTTP_201_CREATED)
async def register_organization(org: OrgCreate, response: Response, db: Session = Depends(get_db)):
    """Cria uma nova conta de organização (precisa de owner_id válido)"""
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set! Check your otb.env file.")

    # Verifica se o owner existe
    owner = db.query(People).filter(People.id == org.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found.")

    # Verifica duplicatas
    if db.query(Organization).filter(Organization.email == org.email).first():
        raise HTTPException(status_code=400, detail="Organization email already registered.")

    if db.query(Organization).filter(Organization.name == org.name).first():
        raise HTTPException(status_code=400, detail="Organization name already taken.")

    # Criptografa senha
    hashed_pwd = ph.hash(org.password)

    # Cria org
    new_org = Organization(
        name=org.name,
        email=org.email,
        password=hashed_pwd,
        owner_id=org.owner_id
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    # Gera JWT
    exp = datetime.utcnow() + timedelta(days=365)
    token = jwt.encode({"org_id": new_org.id, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

    response.set_cookie(
        key="org_jwt",
        value=token,
        httponly=True,
        secure=False,  # True em produção com HTTPS
        samesite="lax",
        max_age=365 * 24 * 60 * 60
    )

    return {"message": "Organization account created successfully."}

class OrgLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/organization/login")
async def login_organization(org: OrgLogin, response: Response, db: Session = Depends(get_db)):
    """Login da conta de organização"""
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set! Check your otb.env file.")

    organization = db.query(Organization).filter(Organization.email == org.email).first()

    if not organization:
        raise HTTPException(status_code=400, detail="Invalid email or password.")

    try:
        ph.verify(str(organization.password), org.password)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid email or password.")

    exp = datetime.utcnow() + timedelta(days=365)
    token = jwt.encode({"org_id": organization.id, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

    response.set_cookie(
        key="org_jwt",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=365 * 24 * 60 * 60
    )

    return {"message": "Organization login successful."}


@router.post("/organization/logout")
async def logout_organization(response: Response):
    """Logout da conta de organização"""

    response.delete_cookie("org_jwt")
    return {"message": "Organization logged out successfully."}