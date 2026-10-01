"""Partido. (REQ 14, 16)"""
import uuid

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    friendly_id: Mapped[str] = mapped_column(ForeignKey("friendlies.id"))
    # "in_progress" | "finished"
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    minute: Mapped[int] = mapped_column(default=0)
    home_score: Mapped[int] = mapped_column(default=0)
    away_score: Mapped[int] = mapped_column(default=0)
    # Estado completo del juego (posiciones, etc.) y lista de eventos (goles, faltas...)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    events: Mapped[list] = mapped_column(JSON, default=list)