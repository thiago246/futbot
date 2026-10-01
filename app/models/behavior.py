"""Comportamientos. (REQ 4, 5)"""
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Behavior(Base):
    __tablename__ = "behaviors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    code: Mapped[str] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(default=True)


class UserBehavior(Base):
    """Qué comportamientos tiene disponibles cada usuario.
    Al registrarse, se le asignan todos los que tienen is_default=True."""

    __tablename__ = "user_behaviors"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    behavior_id: Mapped[int] = mapped_column(ForeignKey("behaviors.id"), primary_key=True)

