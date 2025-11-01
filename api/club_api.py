from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from db.session import SessionLocal
from db.models import Club, Member, ClubMember  # ClubMember = tabela intermediária (muitos-para-muitos)
from api.auth_api import get_current_user
from argon2 import PasswordHasher

router = APIRouter(prefix="/clubs", tags=["Clubs"])
ph = PasswordHasher()

# ------------------ SCHEMAS ------------------

class ClubPublic(BaseModel):
    name: str
    active: bool
    logo: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    
    owner_id: int

    class Config:
        orm_mode = True


class ClubUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class ClubMemberUpdate(BaseModel):
    role: Optional[str] = None  # exemplo: "member", "admin"


# ------------------ DB DEPENDÊNCIA ------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------ ROUTES ------------------

@router.get("/", response_model=List[ClubPublic])
async def list_clubs(db: Session = Depends(get_db)):
    """Retorna uma lista com todos os clubes"""
    return db.query(Club).all()


@router.get("/{club_name}", response_model=ClubPublic)
async def get_club(club_name: str, db: Session = Depends(get_db)):
    """Retorna informações públicas de um clube"""
    club = db.query(Club).filter(Club.name == club_name).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")
    return club


@router.get("/{club_name}/members")
async def list_club_members(club_name: str, db: Session = Depends(get_db)):
    """Retorna todos os membros de um clube"""
    club = db.query(Club).filter(Club.name == club_name).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")
    return [
        {"member_id": cm.member_id, "member_name": cm.member.username, "role": cm.role}
        for cm in club.club_members
    ]


@router.post("/{club_name}/members/{member_name}")
async def add_member_to_club(
    club_name: str,
    member_name: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Adiciona um membro a um clube.
    Somente o dono da CONTA do MEMBER pode se adicionar.
    Clubes NÃO podem adicionar membros.
    """
    current_user, user_type = get_current_user(request, db)

    if user_type != "member":
        raise HTTPException(status_code=403, detail="Only members can join clubs.")

    club = db.query(Club).filter(Club.name == club_name).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    member = db.query(Member).filter(Member.username == member_name).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")
    if member.id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only add yourself to a club.")

    # já é membro?
    existing = db.query(ClubMember).filter_by(club_id=club.id, member_id=member.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Member already belongs to this club.")

    new_assoc = ClubMember(club_id=club.id, member_id=member.id, role="member")
    db.add(new_assoc)
    db.commit()
    return {"message": f"{member.username} joined {club.name} successfully."}


@router.put("/{club_name}")
async def update_club(
    club_name: str,
    data: ClubUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Atualiza informações de um clube — apenas o dono do clube"""
    current_user, user_type = get_current_user(request, db)
    if user_type != "club":
        raise HTTPException(status_code=403, detail="Only club owners can update club info.")

    club = db.query(Club).filter(Club.name == club_name).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")
    if club.id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own club.")

    if data.name:
        if db.query(Club).filter(Club.name == data.name).first():
            raise HTTPException(status_code=400, detail="Club name already taken.")
        club.name = data.name

    if data.email:
        if db.query(Club).filter(Club.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already taken.")
        club.email = data.email

    if data.password:
        club.password = ph.hash(data.password)

    db.commit()
    db.refresh(club)
    return {"message": "Club updated successfully."}


@router.put("/{club_name}/members")
async def update_club_member_role(
    club_name: str,
    data: ClubMemberUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Atualiza o papel de um membro no clube (ex: de member → admin). Apenas o dono do clube."""
    current_user, user_type = get_current_user(request, db)
    if user_type != "club":
        raise HTTPException(status_code=403, detail="Only club owners can update member roles.")

    club = db.query(Club).filter(Club.name == club_name).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")
    if club.id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only manage your own club.")

    if not data.role:
        raise HTTPException(status_code=400, detail="Role is required.")

    # Exemplo simples: apenas update manual (em prática, receberia member_id também)
    raise HTTPException(status_code=501, detail="Role update implementation placeholder.")
    # Aqui você implementaria algo como:
    # assoc = db.query(ClubMember).filter_by(club_id=club.id, member_id=member_id).first()
    # assoc.role = data.role
    # db.commit()


@router.delete("/{club_name}")
async def delete_club(club_name: str, request: Request, db: Session = Depends(get_db)):
    """Deleta um clube — apenas o dono do clube"""
    current_user, user_type = get_current_user(request, db)
    if user_type != "club":
        raise HTTPException(status_code=403, detail="Only club owners can delete clubs.")

    club = db.query(Club).filter(Club.name == club_name).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")
    if club.id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own club.")

    db.delete(club)
    db.commit()
    return {"message": "Club deleted successfully."}


@router.delete("/{club_name}/members/{member_name}")
async def remove_member_from_club(
    club_name: str,
    member_name: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Remove um membro do clube.
    Pode ser feito pelo dono do clube OU pelo próprio membro.
    """
    current_user, user_type = get_current_user(request, db)

    club = db.query(Club).filter(Club.name == club_name).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    member = db.query(Member).filter(Member.username == member_name).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found.")

    assoc = db.query(ClubMember).filter_by(club_id=club.id, member_id=member.id).first()
    if not assoc:
        raise HTTPException(status_code=404, detail="Member is not in this club.")

    # Permissões
    if user_type == "member" and member.id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only remove yourself from a club.")
    if user_type == "club" and club.id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only manage your own club.")

    db.delete(assoc)
    db.commit()
    return {"message": f"{member.username} removed from {club.name}."}
