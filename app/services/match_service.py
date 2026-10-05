"""Lógica de consulta de partidos."""
from sqlalchemy.orm import Session

from app.models.friendly import Friendly
from app.models.match import Match


def get_match(db: Session, match_id: int) -> Match:
    """Estado actual del partido (marcador, minuto, estado, eventos).
    404 si no existe."""
    raise NotImplementedError("REQ 16")


def match_is_watchable(db: Session, match_id: str) -> bool:
    """True si se puede abrir el canal en vivo de ese partido (WS /ws/matches/{id}/live).

    - Si ya existe la fila Match (simulación creada), se puede mirar mientras no haya terminado.
    - Si todavía no existe (cuenta regresiva: la simulación recién arranca), vale el amistoso
      con ese mismo id mientras no esté finalizado.
    - Un partido inexistente o finalizado NO se puede mirar (el canal responde 4404).
    """
    match = db.get(Match, match_id)
    if match is not None:
        return match.status != "finished"
    friendly = db.get(Friendly, match_id)
    return friendly is not None and friendly.status != "finalizado"