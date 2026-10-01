"""Integración real con defaults.py + registry.load_behavior + execute_turn.

No usa dobles para el comportamiento: carga el código tal cual lo escribió la
compañera y verifica que el contexto que arma MatchEngine sea el que esos
comportamientos necesitan.
"""
from types import SimpleNamespace

from app.behaviors.registry import load_behavior
from app.engine.match_engine import MatchEngine

OFENSIVO = '''\
def decidir(contexto):
    if contexto["jugador_con_pelota"] == contexto["mi_id"]:
        patear(contexto["arco_rival"])
    else:
        correr_hacia(contexto["posicion_pelota"])
'''

DEFENSIVO = '''\
def decidir(contexto):
    con_pelota = contexto["jugador_con_pelota"]
    ids_rivales = [r["id"] for r in contexto["jugadores_rivales"]]
    if con_pelota in ids_rivales:
        robar_pelota_jugador(con_pelota)
    else:
        correr_hacia(contexto["posicion_pelota"])
'''


def _player(pid: int, code: str):
    return SimpleNamespace(
        id=pid,
        decide=load_behavior(code),
        strength=60,
        control=60,
        precision=60,
        agility=60,
        speed=60,
    )


def _engine(home_codes, away_codes) -> MatchEngine:
    participants = {
        "home": {"players": [_player(i, c) for i, c in zip((1, 2, 3), home_codes)], "formation": "1-2"},
        "away": {"players": [_player(i, c) for i, c in zip((4, 5, 6), away_codes)], "formation": "2-1"},
    }
    engine = MatchEngine("m1", participants, 1)
    engine.build_initial_state()
    return engine


def test_ofensivo_patea_al_arco_rival_si_tiene_la_pelota():
    engine = _engine([OFENSIVO, OFENSIVO, OFENSIVO], [OFENSIVO, OFENSIVO, OFENSIVO])
    px, py = engine.state.positions["1"]
    engine.state.ball.x, engine.state.ball.y = px + 0.5, py  # "1" tiene la pelota
    engine.execute_behavior("1")
    assert engine.state.ball.vx > 0  # arco rival de home está a la derecha (+x)


def test_ofensivo_corre_hacia_la_pelota_si_no_la_tiene():
    engine = _engine([OFENSIVO, OFENSIVO, OFENSIVO], [OFENSIVO, OFENSIVO, OFENSIVO])
    engine.state.ball.x, engine.state.ball.y = 90.0, 5.0  # lejos de todos
    x0, y0 = engine.state.positions["1"]
    engine.execute_behavior("1")
    x1, y1 = engine.state.positions["1"]
    assert (x1, y1) != (x0, y0)  # se movió


def test_defensivo_roba_si_el_rival_tiene_la_pelota():
    engine = _engine([DEFENSIVO, DEFENSIVO, DEFENSIVO], [OFENSIVO, OFENSIVO, OFENSIVO])
    # "1" (home, DEFENSIVO) con más STRENGTH+CONTROL para ganar el robo sin ambigüedad
    engine._attributes["1"] = {**engine._attributes["1"], "strength": 100, "control": 100}
    px, py = engine.state.positions["4"]
    engine.state.ball.x, engine.state.ball.y = px + 0.3, py  # "4" (rival) tiene la pelota
    engine.state.positions["1"] = (px + 0.1, py)  # "1" está a su lado
    engine.execute_behavior("1")
    assert (engine.state.ball.x, engine.state.ball.y) == engine.state.positions["1"]
    assert (engine.state.ball.vx, engine.state.ball.vy) == (0.0, 0.0)