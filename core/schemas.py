from pydantic import BaseModel
from typing import List, Optional


# ===== SCHEMA PARA TORNEIOS ===== #
class Tournament(BaseModel):
    page: int
    name: str
    id: str
    status: str
    time_control: str
    rating: str
    total_players: str
    organizer: str
    place: str
    fide_players: str
    period: str
    observation: str
    regulation: str


# Schema para torneios da CBX
class CBXTournamentResponse(BaseModel):
    cbx: List[Tournament]

# ===== SCHEMA PARA JOGADORES ===== #
# Futuramente irá ser adicionado otb_id, id do jogador para este site 
class Player(BaseModel):
    name: str
    birthday: str
    gender: str
    country: str
    state: str
    local_id: str
    local_profile: str
    classical: str
    rapid: str
    blitz: str
    fide_id: str

# Schema para Jogadores CBX
class CBXPlayerResponse(BaseModel):
    cbx: List[Player]
    
