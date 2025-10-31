from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


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
    
class TournamentCreate(BaseModel):
    """Schema usado para validar o corpo da requisição POST para criar um novo torneio."""
    
    title: str = Field(..., description="Título ou nome completo do torneio.")
    place: str = Field(..., description="Local de realização (cidade, estado, país).")
    
    # Datas
    start_date: date = Field(..., description="Data de início no formato AAAA-MM-DD.")
    end_date: date = Field(..., description="Data de término no formato AAAA-MM-DD.")
    
    # Detalhes do evento
    time_control: str = Field(..., description="Controle de tempo (ex: Rápido, Clássico, Blitz).")
    rating: str = Field(..., description="Sistema de rating utilizado (ex: FIDE, CBX, Local).")
    image_url: str = Field(..., description="URL para a imagem/cartaz do torneio.")
    
    # Campos Opcionais
    status: Optional[str] = Field("Upcoming", description="Status do torneio (ex: Upcoming, Finished).")
    federation: Optional[str] = Field("local", description="Sigla da federação (padrão: local).")
    external_id: Optional[str] = Field(None, description="ID externo, se aplicável.")
    
    # Exemplo de configuração para facilitar a documentação
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Torneio Aberto de Outono",
                "place": "Rio de Janeiro, RJ, Brasil",
                "start_date": "2025-03-20",
                "end_date": "2025-03-22",
                "time_control": "Clássico (90'+30\")",
                "rating": "CBX",
                "image_url": "https://example.com/poster.jpg"
            }
        }