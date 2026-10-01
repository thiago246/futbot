import pytest

from app.engine.match_state import FIELD_HEIGHT, FIELD_WIDTH, MatchState
from app.engine.player_on_field import PlayerOnField

ATTRS = {"strength": 60, "control": 60, "precision": 60, "agility": 60, "speed": 60}


def _state() -> MatchState:
    return MatchState.initial("m1", 1, ["h1", "h2", "h3"], ["a1", "a2", "a3"], "1-2", "1-2")


def _player(pid: str, state: MatchState, attrs=None) -> PlayerOnField:
    all_attrs = {pid: attrs or ATTRS for pid in state.positions}
    if attrs:
        all_attrs[pid] = attrs
    return PlayerOnField(pid, all_attrs, state)


def test_mover_hacia_avanza_sin_pasarse_de_largo():
    state = _state()
    p = _player("h1", state)
    x0, y0 = p.position
    p.mover_hacia((x0 + 100, y0))  # objetivo lejos: no debe llegar en un tick
    x1, y1 = p.position
    assert x1 > x0 and y1 == y0
    assert x1 - x0 < 100  # no se teletransporta


def test_mover_hacia_no_se_pasa_del_destino_si_esta_cerca():
    state = _state()
    p = _player("h1", state)
    x0, y0 = p.position
    destino = (x0 + 0.1, y0)
    p.mover_hacia(destino)
    assert p.position == destino


def test_mover_hacia_no_sale_de_la_cancha():
    state = _state()
    p = _player("h1", state)
    p.mover_hacia((-1000, -1000))
    x, y = p.position
    assert 0 <= x <= FIELD_WIDTH and 0 <= y <= FIELD_HEIGHT


def test_patear_hacia_fuera_de_alcance_no_hace_nada():
    state = _state()
    state.ball.x, state.ball.y = FIELD_WIDTH, FIELD_HEIGHT  # lejos del jugador h1
    p = _player("h1", state)
    p.patear_hacia((0, 0))
    assert (state.ball.vx, state.ball.vy) == (0.0, 0.0)


def test_patear_hacia_en_alcance_mueve_la_pelota():
    state = _state()
    px, py = state.positions["h1"]
    state.ball.x, state.ball.y = px + 1, py  # dentro del alcance
    p = _player("h1", state)
    p.patear_hacia((px + 10, py))
    assert state.ball.vx > 0
    assert state.ball.vy == pytest.approx(0.0)


def test_intentar_robar_gana_quien_tiene_mas_strength_y_control():
    state = _state()
    fuerte = {**ATTRS, "strength": 100, "control": 100}
    debil = {**ATTRS, "strength": 20, "control": 20}
    all_attrs = {**{pid: ATTRS for pid in state.positions}, "h1": fuerte, "a1": debil}
    ladron = PlayerOnField("h1", all_attrs, state)
    state.ball.vx, state.ball.vy = 5.0, 5.0
    ladron.intentar_robar("a1")
    assert (state.ball.x, state.ball.y) == state.positions["h1"]
    assert (state.ball.vx, state.ball.vy) == (0.0, 0.0)


def test_intentar_robar_pierde_no_toca_la_pelota():
    state = _state()
    debil = {**ATTRS, "strength": 20, "control": 20}
    fuerte = {**ATTRS, "strength": 100, "control": 100}
    all_attrs = {**{pid: ATTRS for pid in state.positions}, "h1": debil, "a1": fuerte}
    ladron = PlayerOnField("h1", all_attrs, state)
    bx, by = state.ball.x, state.ball.y
    ladron.intentar_robar("a1")
    assert (state.ball.x, state.ball.y) == (bx, by)