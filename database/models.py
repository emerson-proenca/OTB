# database/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func
from database.session import Base


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
