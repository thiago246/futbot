import pytest

from app.behaviors.defaults import DEFAULT_BEHAVIORS, DEFENSIVO, EQUILIBRADO, OFENSIVO
from app.behaviors.registry import load_behavior
from app.engine.behavior_executor import execute_turn

BALL = (10, 5)
GOAL = (100, 50)


def ctx(**overrides):
    base = {
        "mi_id": "1",
        "jugador_con_pelota": None,
        "posicion_pelota": BALL,
        "arco_rival": GOAL,
        "jugadores_rivales": [{"id": "9"}],
    }
    return {**base, **overrides}


def run(code, context, player):
    execute_turn(player, load_behavior(code), context)
    return player.calls


@pytest.mark.parametrize("behavior", DEFAULT_BEHAVIORS, ids=lambda b: b["name"])
def test_all_defaults_load(behavior):
    assert callable(load_behavior(behavior["code"]))



def test_offensive_with_ball_kicks_at_goal(player):
    assert run(OFENSIVO, ctx(jugador_con_pelota="1"), player) == [("kick", GOAL)]


def test_offensive_without_ball_runs_to_ball(player):
    assert run(OFENSIVO, ctx(jugador_con_pelota="9"), player) == [("move", BALL)]



def test_defensive_steals_when_rival_has_ball(player):
    calls = run(DEFENSIVO, ctx(jugador_con_pelota="9"), player)
    assert len(calls) == 1
    assert calls[0][0] == "steal"


def test_defensive_runs_to_ball_when_it_is_free(player):
    assert run(DEFENSIVO, ctx(jugador_con_pelota=None), player) == [("move", BALL)]


def test_defensive_runs_to_ball_when_teammate_has_it(player):
    assert run(DEFENSIVO, ctx(jugador_con_pelota="2"), player) == [("move", BALL)]


@pytest.mark.parametrize(
    "context, expected",
    [
        (ctx(jugador_con_pelota="1"), "kick"),
        (ctx(jugador_con_pelota="9"), "steal"),
        (ctx(jugador_con_pelota=None), "move"),
    ],
    ids=["has_ball", "rival_has_ball", "ball_is_free"],
)
def test_balanced_covers_its_three_branches(context, expected, player):
    calls = run(EQUILIBRADO, context, player)
    assert len(calls) == 1
    assert calls[0][0] == expected