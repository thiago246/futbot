import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Club(Base):
    __tablename__ = "clubs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String, nullable=False)
    puntos_ranking = Column(Integer, nullable=False, default=0)
    players = relationship("ClubPlayer", back_populates="club", cascade="all, delete-orphan")
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    user = relationship("User", back_populates="club")