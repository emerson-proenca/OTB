from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from database.session import SessionLocal
from database.models import People

router = APIRouter(tags=["People"])
ph = PasswordHasher()


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(..., min_length=6)

    @field_validator("username")
    def validate_username(cls, v):
        if not re.match("^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain: letters, numbers and underscore (_).")
        return v

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return v


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account."""

    if db.query(People).filter(People.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already in use.")

    if db.query(People).filter(People.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already in use.")

    hashed_password = ph.hash(user.password)

    new_person = People(
        username=user.username,
        email=user.email,
        password=hashed_password
    )

    db.add(new_person)
    db.commit()

    return  # 201 = Created
