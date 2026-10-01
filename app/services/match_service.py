"""Lógica de consulta de partidos."""
from sqlalchemy.orm import Session

from app.models.match import Match


def get_match(db: Session, match_id: int) -> Match:
    """Estado actual del partido (marcador, minuto, estado, eventos).
    404 si no existe."""
    raise NotImplementedError("REQ 16")
