import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    avatar = Column(String, nullable=True)

    club = relationship(
        "Club", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )