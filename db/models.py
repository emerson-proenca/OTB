from sqlalchemy import Column, Date, Integer, String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.session import Base

# =====================
# MODELO MEMBER
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

    # 🔹 Relacionamentos
    owned_clubs: Mapped[list["Club"]] = relationship("Club", back_populates="owner", cascade="all, delete-orphan")
    club_members: Mapped[list["ClubMember"]] = relationship("ClubMember", back_populates="member", cascade="all, delete-orphan")

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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

    # 🔹 Relacionamentos
    owner: Mapped["Member"] = relationship("Member", back_populates="owned_clubs")
    club_members: Mapped[list["ClubMember"]] = relationship("ClubMember", back_populates="club", cascade="all, delete-orphan")

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ClubMember(Base):
    __tablename__ = "club_members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String, default="member")

    # 🔹 Relacionamentos
    club: Mapped["Club"] = relationship("Club", back_populates="club_members")
    member: Mapped["Member"] = relationship("Member", back_populates="club_members")


# TOURNAMENTS
class Tournament(Base):
    __tablename__ = "tournaments"

    # Identificador interno
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Identificação externa e federação
    external_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    federation: Mapped[str | None] = mapped_column(String, index=True, nullable=True)  # e.g. "cbx", "fide"

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

# ===================================================
# THESE TABLES BELOW WILL BE REFACTORED IN THE FUTURE
# ===================================================

# SYNC JOBS
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