import uuid
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class League(Base):
    __tablename__ = "leagues"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String, nullable=False)
    is_private = Column(Boolean, nullable=False, default=False)
    password_hash = Column(String, nullable=True)
    min_teams = Column(Integer, nullable=False)
    max_teams = Column(Integer, nullable=False)
    match_duration = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="esperando_equipos")

    creator_id = Column(String, ForeignKey("users.id"), nullable=False)
    creator = relationship("User")
    members = relationship("LeagueMember", back_populates="league", cascade="all, delete-orphan")


class LeagueMember(Base):
    __tablename__ = "league_members"
    __table_args__ = (UniqueConstraint("league_id", "club_id"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    league_id = Column(String, ForeignKey("leagues.id"), nullable=False)
    club_id = Column(String, ForeignKey("clubs.id"), nullable=False)
    matches_played = Column(Integer, nullable=False, default=0)
    league = relationship("League", back_populates="members")
    club = relationship("Club")