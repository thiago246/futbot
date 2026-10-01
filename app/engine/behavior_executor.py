import logging

from app.behaviors import primitives

logger = logging.getLogger(__name__)


def execute_turn(player, decide, context: dict) -> None:
    """Run decide(context) with `player` as the current player.

    If decide fails, the tick is equivalent to standing still: nothing else is done.
    """
    primitives._set_jugador_actual(player)
    try:
        decide(context)
    except Exception:
        logger.exception("Error in behavior of player %s", getattr(player, "id", "?"))
    finally:
        primitives._set_jugador_actual(None)