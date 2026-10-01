import pytest

from app.behaviors import primitives
from app.behaviors.registry import load_behavior
from app.core.exceptions import BehaviorError
from app.engine.behavior_executor import execute_turn

CONTEXT = {
    "mi_id": "1",
    "jugador_con_pelota": None,
    "posicion_pelota": (10, 5),
    "arco_rival": (100, 50),
    "jugadores_rivales": [],
}

RUN_TO_BALL = "def decidir(contexto):\n    correr_hacia(contexto['posicion_pelota'])\n"


# --- load_behavior ---

def test_load_behavior_returns_decide_function():
    assert callable(load_behavior(RUN_TO_BALL))


def test_load_behavior_without_decidir_fails():
    with pytest.raises(BehaviorError):
        load_behavior("x = 1")


def test_load_behavior_with_syntax_error_fails():
    with pytest.raises(BehaviorError):
        load_behavior("def decidir(contexto) return 1")


def test_load_behavior_blocks_imports():
    with pytest.raises(BehaviorError):
        load_behavior("import os\ndef decidir(c): pass")


# --- execute_turn ---

def test_execute_turn_applies_primitives_to_player(player):
    execute_turn(player, load_behavior(RUN_TO_BALL), CONTEXT)
    assert player.calls == [("move", (10, 5))]


def test_execute_turn_swallows_exception_and_does_nothing(player):
    decide = load_behavior("def decidir(contexto):\n    1 / 0\n")
    execute_turn(player, decide, CONTEXT)  # must not raise
    assert player.calls == []


def test_execute_turn_clears_current_player(player):
    execute_turn(player, lambda ctx: None, CONTEXT)
    with pytest.raises(RuntimeError):
        primitives._get_jugador_actual()


def test_execute_turn_clears_current_player_even_on_failure(player):
    execute_turn(player, lambda ctx: 1 / 0, CONTEXT)
    with pytest.raises(RuntimeError):
        primitives._get_jugador_actual()


def test_execute_turn_does_not_leak_player_between_turns(player):
    other = type(player)()
    execute_turn(player, load_behavior(RUN_TO_BALL), CONTEXT)
    execute_turn(other, load_behavior(RUN_TO_BALL), CONTEXT)
    assert len(player.calls) == 1
    assert len(other.calls) == 1