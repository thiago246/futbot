"""Amistoso (publicación previa al partido). (REQ 11 a 14)

Un Friendly nace en "esperando_rival" (POST /matches), pasa a "programado"
cuando otro club se une, y a "en_curso" cuando se inicia. Al iniciarse se crea
el Match (simulación) que apunta a este Friendly.

Los valores de kind (tipo) y status (estado) son los del contrato.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.core.database import Base

class Friendly(Base):
    __tablename__ = "friendlies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # "amistoso" (el contrato también prevé "liga", que no se maneja acá)
    kind = Column(String, nullable=False, default="amistoso")
    # "esperando_rival" | "programado" | "cuenta_regresiva" | "en_curso" | "pausado" | "finalizado"
    status = Column(String, nullable=False, default="esperando_rival")
    home_club_id = Column(String, ForeignKey("clubs.id"), nullable=False)
    away_club_id = Column(String, ForeignKey("clubs.id"), nullable=True)
    duration = Column(Integer, nullable=False)  # minutos: 1, 3 o 5
    home_score = Column(Integer, nullable=False, default=0)
    away_score = Column(Integer, nullable=False, default=0)
    remaining_substitutions = Column(Integer, nullable=False, default=3)
    # Solo para ordenar el listado (no se expone en la API)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))