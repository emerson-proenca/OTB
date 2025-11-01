from sqlalchemy import Column, Date, Integer, String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.session import Base

# =====================
# MEMBER MODEL
# =====================
class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    name: Mapped[str | None] = mapped_column(String)
    gender: Mapped[str | None] = mapped_column(String)
    birthdate: Mapped[str | None] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)
    active: Mapped[int] = mapped_column(Integer, default=1)
    role: Mapped[str] = mapped_column(String, default="player")
    profile_picture: Mapped[str | None] = mapped_column(String)
    rating_id: Mapped[str | None] = mapped_column(String)
    bio: Mapped[str | None] = mapped_column(Text)
    
    national_id: Mapped[str | None] = mapped_column(String)
    fide_id: Mapped[str | None] = mapped_column(String)

    # Relationships
    owned_clubs: Mapped[list["Club"]] = relationship("Club", back_populates="owner", cascade="all, delete-orphan")
    club_members: Mapped[list["ClubMember"]] = relationship("ClubMember", back_populates="member", cascade="all, delete-orphan")

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# =====================
# CLUB MODEL
# =====================

class Club(Base):
    __tablename__ = "clubs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String(100))
    logo: Mapped[str | None] = mapped_column(String)
    active: Mapped[int] = mapped_column(Integer, default=1)

    owner_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    owner: Mapped["Member"] = relationship("Member", back_populates="owned_clubs")
    club_members: Mapped[list["ClubMember"]] = relationship("ClubMember", back_populates="club", cascade="all, delete-orphan")

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# =====================
# TOURNAMENT MODEL
# =====================

class Tournament(Base):
    __tablename__ = "tournaments"

    # Identificador interno
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Identificação externa e federação
    external_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    federation: Mapped[str | None] = mapped_column(String, index=True, nullable=True)  # e.g. "fide"

    # Informações gerais
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    total_players: Mapped[str | None] = mapped_column(String, nullable=True)
    organizer: Mapped[str | None] = mapped_column(String, nullable=True)
    place: Mapped[str | None] = mapped_column(String, nullable=True)
    fide_players: Mapped[str | None] = mapped_column(String, nullable=True)
    period: Mapped[str | None] = mapped_column(String, nullable=True)
    observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    regulation: Mapped[str | None] = mapped_column(String, nullable=True)
    start_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    time_control: Mapped[str | None] = mapped_column(String, nullable=True)
    rating: Mapped[str | None] = mapped_column(String, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Chave estrangeira para o clube
    club_id: Mapped[int | None] = mapped_column(ForeignKey("clubs.id", ondelete="SET NULL"), nullable=True)

    # Datas e metadados
    year: Mapped[str | None] = mapped_column(String, nullable=True)
    month: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    scraped_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamento com o clube
    club: Mapped["Club"] = relationship("Club", backref="tournaments")

    __table_args__ = (
        UniqueConstraint("federation", "external_id", name="uix_fed_externalid"),
    )

# =====================
# GAME MODEL
# =====================

class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    white_player_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="SET NULL"), nullable=True)
    black_player_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="SET NULL"), nullable=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="SET NULL"), nullable=True)
    result: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "1-0", "0-1", "1/2-1/2"
    round: Mapped[int | None] = mapped_column(Integer, nullable=True)
    board_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    utc_datetime: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    white_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    black_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    white_rating_change: Mapped[int | None] = mapped_column(Integer, nullable=True)
    black_rating_change: Mapped[int | None] = mapped_column(Integer, nullable=True)
    variant: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "Classical", "Blitz"
    time_control: Mapped[str | None] = mapped_column(String, nullable=True)
    termination: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "Checkmate", "Time forfeit"
    opening_name: Mapped[str | None] = mapped_column(String, nullable=True)
    opening_eco: Mapped[str | None] = mapped_column(String, nullable=True)
    
    moves: Mapped[Text | None] = mapped_column(Text, nullable=True)   # PGN or move list
    played_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relacionamentos
    white_player: Mapped["Member"] = relationship("Member", foreign_keys=[white_player_id], backref="games_as_white")
    black_player: Mapped["Member"] = relationship("Member", foreign_keys=[black_player_id], backref="games_as_black")
    tournament: Mapped["Tournament"] = relationship("Tournament", backref="games")


# =====================
# ASSOCIATIVE TABLES
# =====================

class TournamentMember(Base):
    __tablename__ = "tournament_members"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    
    # Relacionamentos
    tournament: Mapped["Tournament"] = relationship("Tournament", backref="tournament_members")
    member: Mapped["Member"] = relationship("Member", backref="tournament_members")
    

class ClubMember(Base):
    __tablename__ = "club_members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String, default="member")

    # Relacionamentos
    club: Mapped["Club"] = relationship("Club", back_populates="club_members")
    member: Mapped["Member"] = relationship("Member", back_populates="club_members")
    
    
class ClubTournament(Base):
    __tablename__ = "club_tournaments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False)

    # Relacionamentos
    club: Mapped["Club"] = relationship("Club", backref="club_tournaments")
    tournament: Mapped["Tournament"] = relationship("Tournament", backref="club_tournaments")    
    
    
class RatingHistory(Base):
    __tablename__ = "rating_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False)
    
    # FIDE
    classical_fide: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rapid_fide: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blitz_fide: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # NATIONAL
    classical_national: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rapid_national: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blitz_national: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bullet_national: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # CHESSCOM
    rapid_chesscom: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blitz_chesscom: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bullet_chesscom: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # LICHESS
    classical_lichess: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rapid_lichess: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blitz_lichess: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bullet_lichess: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Relacionamento
    member: Mapped["Member"] = relationship("Member", backref="rating_history")  


