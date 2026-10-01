"""Tests de MatchEngine con stubs livianos (sin DB real).

Para la integración con la base de datos, ver test_match_engine_persist.py.
Para la integración con los comportamientos default reales, ver
test_default_behaviors_integration.py.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.engine.match_engine import MatchEngine
from app.engine.match_state import FIELD_HEIGHT, FIELD_WIDTH, GOAL_Y_MIN, TICKS_PER_MINUTE


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _quieto(contexto):
    """Comportamiento que no hace nada (no importa la física a probar)."""
    return None


def _players(*ids):
    return [
        SimpleNamespace(id=i, decide=_quieto, strength=60, control=60, precision=60, agility=60, speed=60)
        for i in ids
    ]


def _engine(duration_minutes=1) -> MatchEngine:
    participants = {
        "home": {"players": _players(1, 2, 3), "formation": "1-2"},
        "away": {"players": _players(4, 5, 6), "formation": "2-1"},
    }
    return MatchEngine("m1", participants, duration_minutes)


def _engine_started(duration_minutes=1) -> MatchEngine:
    engine = _engine(duration_minutes)
    engine.build_initial_state()
    return engine


# --------------------------------------------------------------------- ciclo de vida
def test_antes_de_arrancar_no_hay_estado():
    assert _engine().state is None


def test_build_initial_state_guarda_el_estado_en_memoria():
    engine = _engine()
    state = engine.build_initial_state()
    assert engine.state is state
    assert set(state.positions) == {"1", "2", "3", "4", "5", "6"}
    assert (state.home_score, state.away_score, state.current_tick) == (0, 0, 0)


def test_build_initial_state_respeta_el_orden_y_la_formacion():
    from app.engine.match_state import FORMATIONS

    state = _engine().build_initial_state()
    assert state.positions["1"] == FORMATIONS["1-2"][0]
    assert state.positions["4"][1] == FORMATIONS["2-1"][0][1]


def test_discard_state_lo_elimina_por_completo():
    engine = _engine()
    engine.build_initial_state()
    engine.discard_state()
    assert engine.state is None


def test_prepara_jugadores_una_sola_vez_al_construir_el_estado():
    engine = _engine_started()
    assert set(engine._player_ids) == {"1", "2", "3", "4", "5", "6"}
    assert engine._sides["1"] == "home" and engine._sides["4"] == "away"
    assert engine._decide_fns["1"] is _quieto


def test_jugador_sin_decide_ni_behavior_code_falla_al_prepararse():
    participants = {
        "home": {"players": [SimpleNamespace(id=1, strength=60, control=60, precision=60, agility=60, speed=60)], "formation": "1-2"},
        "away": {"players": _players(4, 5, 6), "formation": "2-1"},
    }
    engine = MatchEngine("m1", participants, 1)
    with pytest.raises(ValueError):
        engine.build_initial_state()


def test_jugador_sin_alguna_pacss_falla_al_prepararse():
    """Las 5 PACSS son requisito para entrar a un partido: no hay valor por
    defecto, así que si falta una, se cae con un error claro (no en silencio)."""
    incompleto = SimpleNamespace(id=1, decide=_quieto, strength=60, control=60, agility=60, speed=60)
    participants = {
        "home": {"players": [incompleto, *_players(2, 3)], "formation": "1-2"},
        "away": {"players": _players(4, 5, 6), "formation": "2-1"},
    }
    engine = MatchEngine("m1", participants, 1)
    with pytest.raises(AttributeError):
        engine.build_initial_state()


# --------------------------------------------------------------------- tick y física
def test_tick_avanza_el_contador():
    engine = _engine_started()
    engine.tick()
    assert engine.state.current_tick == 1
    engine.tick()
    assert engine.state.current_tick == 2


def test_pelota_rebota_arriba_y_abajo():
    engine = _engine_started()
    engine.state.ball.x, engine.state.ball.y = FIELD_WIDTH / 2, 1.0
    engine.state.ball.vx, engine.state.ball.vy = 0.0, -5.0
    engine.tick()
    assert engine.state.ball.y > 0
    assert engine.state.ball.vy > 0  # se invirtió


def test_pelota_rebota_en_el_costado_fuera_del_arco():
    engine = _engine_started()
    engine.state.ball.x, engine.state.ball.y = 1.0, 5.0  # fuera del rango del arco
    engine.state.ball.vx, engine.state.ball.vy = -5.0, 0.0
    engine.tick()
    assert engine.state.ball.x > 0
    assert engine.state.ball.vx > 0
    assert (engine.state.home_score, engine.state.away_score) == (0, 0)


def test_gol_del_visitante_en_el_arco_local():
    engine = _engine_started()
    engine.state.ball.x, engine.state.ball.y = 1.0, GOAL_Y_MIN + 1
    engine.state.ball.vx, engine.state.ball.vy = -5.0, 0.0
    engine.tick()
    assert engine.state.away_score == 1
    assert engine.state.home_score == 0
    assert (engine.state.ball.x, engine.state.ball.y) == (FIELD_WIDTH / 2, FIELD_HEIGHT / 2)
    assert (engine.state.ball.vx, engine.state.ball.vy) == (0.0, 0.0)


def test_gol_del_local_en_el_arco_visitante():
    engine = _engine_started()
    engine.state.ball.x, engine.state.ball.y = FIELD_WIDTH - 1, GOAL_Y_MIN + 1
    engine.state.ball.vx, engine.state.ball.vy = 5.0, 0.0
    engine.tick()
    assert engine.state.home_score == 1
    assert engine.state.away_score == 0


def test_is_finished_solo_al_llegar_a_la_duracion():
    engine = _engine_started(duration_minutes=1)
    assert not engine.is_finished()
    for _ in range(TICKS_PER_MINUTE):
        engine.tick()
    assert engine.is_finished()


def test_execute_behavior_arma_contexto_con_rivales_y_companeros():
    engine = _engine_started()
    capturado = {}

    def espia(contexto):
        capturado.update(contexto)

    engine._decide_fns["1"] = espia
    engine.execute_behavior("1")
    assert capturado["mi_id"] == "1"
    assert len(capturado["jugadores_companeros"]) == 2
    assert len(capturado["jugadores_rivales"]) == 3
    assert all(r["id"] != "1" for r in capturado["jugadores_companeros"])
    assert capturado["arco_rival"] == (FIELD_WIDTH, FIELD_HEIGHT / 2)


def test_jugador_con_pelota_es_none_si_esta_libre():
    engine = _engine_started()
    engine.state.ball.x, engine.state.ball.y = FIELD_WIDTH / 2, FIELD_HEIGHT / 2
    assert engine._player_with_ball() is None


def test_jugador_con_pelota_es_quien_esta_en_su_alcance():
    engine = _engine_started()
    px, py = engine.state.positions["1"]
    engine.state.ball.x, engine.state.ball.y = px + 0.5, py
    assert engine._player_with_ball() == "1"


def test_arco_rival_correcto_por_lado():
    engine = _engine_started()
    assert engine._rival_goal("home") == (FIELD_WIDTH, FIELD_HEIGHT / 2)
    assert engine._rival_goal("away") == (0.0, FIELD_HEIGHT / 2)


# --------------------------------------------------------------------------- run()
@pytest.mark.anyio
async def test_run_construye_el_estado_si_no_existe():
    engine = _engine()
    with patch("app.engine.match_engine.manager.broadcast", new_callable=AsyncMock), \
         patch.object(MatchEngine, "_persist_state"), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        await engine.run()
    assert engine.state is None  # se descartó al finalizar


@pytest.mark.anyio
async def test_run_hace_tick_hasta_terminar_y_descarta_el_estado():
    engine = _engine_started(duration_minutes=1)
    with patch("app.engine.match_engine.manager.broadcast", new_callable=AsyncMock) as bc, \
         patch.object(MatchEngine, "_persist_state") as persist, \
         patch("asyncio.sleep", new_callable=AsyncMock) as sleep:
        await engine.run()
    assert sleep.await_count == TICKS_PER_MINUTE
    assert bc.await_count == TICKS_PER_MINUTE + 1  # + 1 final de "finished"
    assert bc.await_args_list[-1].args[1]["type"] == "finished"
    assert persist.call_count == TICKS_PER_MINUTE + 1
    assert persist.call_args_list[-1].kwargs == {"final": True}
    assert engine.state is None


@pytest.mark.anyio
async def test_run_no_hace_nada_si_ya_estaba_terminado():
    engine = _engine_started(duration_minutes=1)
    engine.state.current_tick = TICKS_PER_MINUTE
    with patch("app.engine.match_engine.manager.broadcast", new_callable=AsyncMock) as bc, \
         patch.object(MatchEngine, "_persist_state") as persist, \
         patch("asyncio.sleep", new_callable=AsyncMock) as sleep:
        await engine.run()
    assert sleep.await_count == 0
    assert bc.await_count == 1  # solo el "finished"
    assert persist.call_count == 1