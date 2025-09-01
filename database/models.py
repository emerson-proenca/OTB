# database/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func
from database.session import Base
from datetime import datetime, timezone


# TOURNAMENTS
class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, index=True)  # internal id

    # original id fornecido pela federação (ex: CBX ID)
    external_id = Column(String, index=True, nullable=True)
    federation = Column(String, index=True, nullable=False)  # e.g. "cbx", "fide"
    name = Column(String, nullable=False)
    status = Column(String, nullable=True)
    time_control = Column(String, nullable=True)
    rating = Column(String, nullable=True)
    total_players = Column(Integer, nullable=True)
    organizer = Column(String, nullable=True)
    place = Column(String, nullable=True)
    fide_players = Column(Integer, nullable=True)
    period = Column(String, nullable=True)
    observation = Column(Text, nullable=True)
    regulation = Column(String, nullable=True)

    year = Column(String, nullable=True)
    month = Column(String, nullable=True)

    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

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
