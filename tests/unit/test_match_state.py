import pytest

from app.engine.match_state import (
    FIELD_HEIGHT,
    FIELD_WIDTH,
    FORMATIONS,
    MatchState,
)

D = 3  # duración de uso general en los tests

HOME = ["h1", "h2", "h3"]
AWAY = ["a1", "a2", "a3"]
F = "1-2"  # formación de uso general en los tests


def test_estado_inicial_tiene_6_jugadores_y_pelota_al_centro():
    e = MatchState.initial("m1", D, HOME, AWAY, F, F)
    assert set(e.positions) == set(HOME + AWAY)
    assert (e.ball.x, e.ball.y) == (FIELD_WIDTH / 2, FIELD_HEIGHT / 2)


def test_estado_inicial_arranca_en_0():
    e = MatchState.initial("m1", D, HOME, AWAY, F, F)
    assert (e.home_score, e.away_score, e.current_tick) == (0, 0, 0)


def test_posiciones_dentro_de_la_cancha_y_away_espejado():
    e = MatchState.initial("m1", D, HOME, AWAY, F, F)
    for x, y in e.positions.values():
        assert 0 <= x <= FIELD_WIDTH and 0 <= y <= FIELD_HEIGHT
    for h, a in zip(HOME, AWAY):
        assert e.positions[a] == (FIELD_WIDTH - e.positions[h][0], e.positions[h][1])


def test_rechaza_cantidad_incorrecta_o_repetidos():
    with pytest.raises(ValueError):
        MatchState.initial("m1", D, ["a", "b"], AWAY, F, F)
    with pytest.raises(ValueError):
        MatchState.initial("m1", D, HOME, ["h1", "a2", "a3"], F, F)


def test_cada_club_usa_su_formacion():
    e = MatchState.initial("m1", D, HOME, AWAY, home_formation="2-1", away_formation="1-2")
    assert e.positions["h1"] == FORMATIONS["2-1"][0]
    x, y = FORMATIONS["1-2"][2]
    assert e.positions["a3"] == (FIELD_WIDTH - x, y)


def test_todas_las_formaciones_tienen_3_posiciones_dentro_de_la_cancha():
    for name, positions in FORMATIONS.items():
        assert len(positions) == 3, name
        assert all(0 <= x <= FIELD_WIDTH / 2 and 0 <= y <= FIELD_HEIGHT for x, y in positions)


def test_rechaza_formacion_desconocida():
    with pytest.raises(ValueError):
        MatchState.initial("m1", D, HOME, AWAY, "9-9-9", F)


def test_la_formacion_es_obligatoria():
    with pytest.raises(TypeError):
        MatchState.initial("m1", D, HOME, AWAY)


def test_is_over_solo_cuando_se_alcanza_la_duracion():
    from app.engine.match_state import TICKS_PER_MINUTE

    e = MatchState.initial("m1", 1, HOME, AWAY, F, F)
    assert not e.is_over()
    e.current_tick = TICKS_PER_MINUTE - 1
    assert not e.is_over()
    e.current_tick = TICKS_PER_MINUTE
    assert e.is_over()


def test_duracion_invalida_lanza_error():
    with pytest.raises(ValueError):
        MatchState.initial("m1", 0, HOME, AWAY, F, F)