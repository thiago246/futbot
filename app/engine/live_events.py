"""Mensajes del canal en vivo de un partido (REQ 16, versión simplificada).

Solo ARMA los mensajes del contrato AsyncAPI (`tick` y `partido_finalizado`) y el nombre
de la sala; no envía nada ni toca la base de datos. Quien emite es MatchEngine.

Sin pausas ni sustituciones en este sprint: no existen pausa_iniciada ni
sustitucion_realizada.
"""
from app.engine.match_state import TICKS_PER_MINUTE, MatchState


def match_room(match_id: str) -> str:
    """Sala del ConnectionManager. `match_id` es el id del amistoso (el matchId de la API)."""
    return f"match:{match_id}"


def tick_event(state: MatchState) -> dict:
    """Estado del partido en este tick.

    local = club home (el creador), visitante = club away.
    tiempoRestante en segundos: 1 tick = 1 segundo, nunca negativo.
    """
    total_ticks = state.duration_minutes * TICKS_PER_MINUTE
    return {
        "tipo": "tick",
        "pelota": {"x": state.ball.x, "y": state.ball.y},
        "posiciones": [
            {"jugadorId": player_id, "x": x, "y": y}
            for player_id, (x, y) in state.positions.items()
        ],
        "marcador": {"local": state.home_score, "visitante": state.away_score},
        "tiempoRestante": max(0, total_ticks - state.current_tick),
    }


def match_finished_event(state: MatchState) -> dict:
    return {
        "tipo": "partido_finalizado",
        "resultado": {"local": state.home_score, "visitante": state.away_score},
    }
