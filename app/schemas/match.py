"""Formatos de partido. (REQ 16)  También es el formato de los mensajes por WebSocket."""
from pydantic import BaseModel, ConfigDict


class MatchEvent(BaseModel):
    minute: int
    type: str          # "goal", "foul", ...
    description: str = ""


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    friendly_id: str
    status: str        # "in_progress" | "finished"
    minute: int
    home_score: int
    away_score: int
    state: dict = {}   # posiciones, etc.
    events: list = []
