from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from db.session import SessionLocal
from db.models import Member
from apis.auth_api import get_current_user
from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions

router = APIRouter(prefix="/api/members", tags=["Members"])
ph = PasswordHasher()

# ------------------ SCHEMAS ------------------

class MemberPublic(BaseModel):
    username: str
    email: EmailStr

    class Config:
        orm_mode = True


class MemberUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


# ------------------ DEPENDÊNCIA DB ------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------ ROUTES ------------------

@router.get("/", response_model=List[MemberPublic])
async def list_members(db: Session = Depends(get_db)):
    """Retorna todos os membros (apenas públicos)"""
    members = db.query(Member).all()
    return members


@router.get("/{member_name}", response_model=MemberPublic)
async def get_member(member_name: str, db: Session = Depends(get_db)):
    """Retorna informações de um único membro"""
    member = db.query(Member).filter(Member.username == member_name).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    return member


@router.put("/{member_name}")
async def update_member(
    member_name: str,
    data: MemberUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Atualiza o perfil do membro — somente o dono pode"""
    current_user, user_type = get_current_user(request, db)

    if user_type != "member":
        raise HTTPException(status_code=403, detail="Only members can update member profiles.")

    member = db.query(Member).filter(Member.username == member_name).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    if member.id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own account.")

    # Atualização condicional dos campos
    if data.username:
        if db.query(Member).filter(Member.username == data.username).first():
            raise HTTPException(status_code=400, detail="Username already taken.")
        member.username = data.username

    if data.email:
        if db.query(Member).filter(Member.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already taken.")
        member.email = data.email

    if data.password:
        member.password = ph.hash(data.password)

    db.commit()
    db.refresh(member)
    return {"message": "Member updated successfully."}


@router.delete("/{member_name}")
async def delete_member(member_name: str, request: Request, db: Session = Depends(get_db)):
    """Deleta o membro logado — somente o dono pode"""
    current_user, user_type = get_current_user(request, db)

    if user_type != "member":
        raise HTTPException(status_code=403, detail="Only members can delete member profiles.")

    member = db.query(Member).filter(Member.username == member_name).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    if member.id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own account.")

    db.delete(member)
    db.commit()
    return {"message": "Member deleted successfully."}
