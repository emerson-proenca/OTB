# database/models.py
from sqlalchemy import Column, Date, Integer, String, DateTime, Text, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.session import Base


# TOURNAMENTS
class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, index=True)  # internal id


    # original id fornecido pela federação (ex: CBX ID)
    external_id = Column(String, index=True, nullable=True)

    federation = Column(String, index=True, nullable=True)  # e.g. "cbx", "fide"
    title = Column(String, nullable=True)
    status = Column(String, nullable=True)

    total_players = Column(String, nullable=True)
    organizer = Column(String, nullable=True)
    place = Column(String, nullable=True)
    fide_players = Column(String, nullable=True)
    period = Column(String, nullable=True)
    observation = Column(Text, nullable=True)
    regulation = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    time_control = Column(String, nullable=True)
    rating = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    club_id = Column(Integer, ForeignKey("Club.id"), nullable=True)

    year = Column(String, nullable=True)
    month = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    club = relationship("Club", backref="tournament")

    __table_args__ = (
        UniqueConstraint("federation", "external_id", name="uix_fed_externalid"),
    )


# PLAYERS
class CBXPlayer(Base):
    __tablename__ = "cbx_players"

    id = Column(Integer, primary_key=True, index=True)
    local_id = Column(String, index=True, nullable=False)
    fide_id = Column(String, index=True, nullable=True)
    name = Column(String, nullable=False)
    birthday = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    country = Column(String, nullable=True)
    state = Column(String, nullable=True)
    classical = Column(String, nullable=True)
    rapid = Column(String, nullable=True)
    blitz = Column(String, nullable=True)
    local_profile = Column(String, nullable=True)

    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# ANNOUNCEMENTS
class CBXAnnouncement(Base):
    __tablename__ = "cbx_announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    date_text = Column(String, nullable=True)    # data apresentada no site (texto)
    link = Column(String, nullable=False, unique=True, index=True)  # usamos link como chave natural
    content = Column(Text, nullable=True)        # futuro: você pode baixar o conteúdo do comunicado
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("link", name="uix_announcement_link"),
    )

# NEWS
class CBXNews(Base):
    __tablename__ = "cbx_news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    date_text = Column(String, nullable=True)
    link = Column(String, nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # futuro: full content crawled from link
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("link", name="uix_news_link"),
    )


# SYNC JOB
class SyncJob(Base):
    __tablename__ = "sync_jobs"
    id = Column(Integer, primary_key=True, index=True)
    federation = Column(String, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False)   # e.g. "started", "success", "partial", "failed"
    created = Column(Integer, nullable=True)
    updated = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)

# =====================
#   MODELO: PESSOAS
# =====================
class Member(Base):
    __tablename__ = "member"

    id = Column(Integer, primary_key=True, index=True)

    # Dados de login e segurança
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    # Dados de perfil
    name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    birthdate = Column(String, nullable=True)
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    active = Column(Integer, default=1)  # 1 = ativo, 0 = inativo
    role = Column(String, default="player")  # player, organizer, admin etc.
    profile_picture = Column(String, nullable=True)
    rating_id = Column(String, nullable=True)  # FIDE ID, CBX ID etc.
    bio = Column(Text, nullable=True)
    # social_links = Column(Text, nullable=True)  # JSON string with social media links


    # Relacionamentos
    Club = relationship("Club", back_populates="owner", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==========================
#   MODELO: CLUBES
# ==========================
class Club(Base):
    __tablename__ = "Club"

    id = Column(Integer, primary_key=True, index=True)

    # Dados de login e segurança
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    # Dados de perfil
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    logo = Column(String, nullable=True)
    active = Column(Integer, default=1)  # 1 = ativa, 0 = inativa
    description = Column(String(100), nullable=True) # Short description, up to 100 chars
    # social_links = Column(Text, nullable=True)  # JSON string with social media links
    # markdown = Column(Text, nullable=True)  # Detailed description in Markdown

    # FK para o dono do clube (Pessoa)
    owner_id = Column(Integer, ForeignKey("member.id", ondelete="CASCADE"), nullable=False)

    # Relacionamento inverso
    owner = relationship("Member", back_populates="Club")

    created_at = Column(DateTime(timezone=True), server_default=func.now())