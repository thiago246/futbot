import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClubPlayer(Base):
    __tablename__ = "club_players"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    strength = Column(Integer, nullable=False)
    control = Column(Integer, nullable=False)
    precision = Column(Integer, nullable=False)
    agility = Column(Integer, nullable=False)
    speed = Column(Integer, nullable=False)

    club_id = Column(String, ForeignKey("clubs.id"), nullable=False)
    club = relationship("Club", back_populates="players")