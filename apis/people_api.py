from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from database.session import SessionLocal
from database.models import People

router = APIRouter(tags=["People"])
ph = PasswordHasher()


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Cria um novo usuário (API pura)"""

    if db.query(People).filter(People.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado.")

    if db.query(People).filter(People.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username já cadastrado.")

    hashed_password = ph.hash(user.password)

    new_person = People(
        username=user.username,
        email=user.email,
        password=hashed_password
    )

    db.add(new_person)
    db.commit()

    return  # 201 = Created
