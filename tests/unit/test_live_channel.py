"""Canal en vivo del partido (REQ 16): mensajes, cierre de sala y emisión del motor.

Usa sockets falsos registrados directo en el ConnectionManager (sin TestClient),
así el motor corre en el mismo event loop que los tests.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import app.engine.match_engine as match_engine_module
from app.core.ws_manager import manager
from app.engine.live_events import match_finished_event, match_room, tick_event
from app.engine.match_engine import MatchEngine
from app.engine.match_state import FIELD_HEIGHT, FIELD_WIDTH, TICKS_PER_MINUTE, MatchState


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def clean_rooms():
    manager.rooms.clear()
    yield
    manager.rooms.clear()


class FakeWS:
    def __init__(self, fail_close: bool = False):
        self.sent: list[dict] = []
        self.closed_with: int | None = None
        self.fail_close = fail_close

    async def accept(self):
        pass

    async def send_json(self, message: dict):
        self.sent.append(message)

    async def close(self, code: int = 1000):
        if self.fail_close:
            raise RuntimeError("ya estaba caído")
        self.closed_with = code


def _quieto(contexto):
    return None


def _players(*ids):
    return [
        SimpleNamespace(id=i, decide=_quieto, strength=60, control=60, precision=60, agility=60, speed=60)
        for i in ids
    ]


def _engine(duration_minutes=1, match_id="m1") -> MatchEngine:
    participants = {
        "home": {"players": _players(1, 2, 3), "formation": "1-2"},
        "away": {"players": _players(4, 5, 6), "formation": "2-1"},
    }
    return MatchEngine(match_id, participants, duration_minutes)


def _state(duration=1) -> MatchState:
    return MatchState.initial("m1", duration, ["1", "2", "3"], ["4", "5", "6"], "1-2", "2-1")


# ------------------------------------------------------------------ mensajes
def test_tick_event_tiene_la_forma_del_contrato():
    state = _state()
    state.home_score, state.away_score = 2, 1
    msg = tick_event(state)
    assert set(msg) == {"tipo", "pelota", "posiciones", "marcador", "tiempoRestante"}
    assert msg["tipo"] == "tick"
    assert msg["pelota"] == {"x": FIELD_WIDTH / 2, "y": FIELD_HEIGHT / 2}
    assert msg["marcador"] == {"local": 2, "visitante": 1}


def test_tick_event_posiciones_es_lista_con_los_6_jugadores():
    msg = tick_event(_state())
    assert isinstance(msg["posiciones"], list) and len(msg["posiciones"]) == 6
    assert all(set(p) == {"jugadorId", "x", "y"} for p in msg["posiciones"])
    assert {p["jugadorId"] for p in msg["posiciones"]} == {"1", "2", "3", "4", "5", "6"}


def test_tiempo_restante_es_duracion_menos_ticks():
    state = _state(duration=3)
    assert tick_event(state)["tiempoRestante"] == 3 * TICKS_PER_MINUTE
    state.current_tick = 45
    assert tick_event(state)["tiempoRestante"] == 3 * TICKS_PER_MINUTE - 45


def test_tiempo_restante_nunca_es_negativo():
    state = _state()
    state.current_tick = TICKS_PER_MINUTE + 10
    assert tick_event(state)["tiempoRestante"] == 0


def test_partido_finalizado_lleva_el_resultado_exacto():
    state = _state()
    state.home_score, state.away_score = 3, 3
    assert match_finished_event(state) == {
        "tipo": "partido_finalizado",
        "resultado": {"local": 3, "visitante": 3},
    }


def test_match_room():
    assert match_room("abc") == "match:abc"


# ------------------------------------------------------------- cierre de sala
@pytest.mark.anyio
async def test_close_room_cierra_a_todos_y_elimina_la_sala():
    a, b = FakeWS(), FakeWS()
    manager.rooms["match:x"] = [a, b]
    await manager.close_room("match:x")
    assert a.closed_with == 1000 and b.closed_with == 1000
    assert "match:x" not in manager.rooms


@pytest.mark.anyio
async def test_close_room_sigue_si_un_socket_falla():
    roto, sano = FakeWS(fail_close=True), FakeWS()
    manager.rooms["match:x"] = [roto, sano]
    await manager.close_room("match:x")
    assert sano.closed_with == 1000


@pytest.mark.anyio
async def test_close_room_de_sala_inexistente_no_hace_nada():
    await manager.close_room("match:no-existe")


@pytest.mark.anyio
async def test_schedule_close_cierra_recien_despues_del_delay():
    ws = FakeWS()
    manager.rooms["match:x"] = [ws]
    manager.schedule_close("match:x", 0.05)
    await asyncio.sleep(0.01)
    assert ws.closed_with is None
    await asyncio.sleep(0.1)
    assert ws.closed_with == 1000
    assert "match:x" not in manager.rooms


# ----------------------------------------------------------------- el motor
@pytest.mark.anyio
async def test_run_emite_ticks_y_partido_finalizado_a_la_sala():
    ws = FakeWS()
    manager.rooms["match:f1"] = [ws]
    engine = _engine(duration_minutes=1, match_id="f1")
    with patch.object(match_engine_module, "TICK_SECONDS", 0), \
         patch.object(match_engine_module, "ROOM_CLOSE_DELAY_SECONDS", 0.05), \
         patch.object(MatchEngine, "_persist_state"):
        await engine.run()

    tipos = [m["tipo"] for m in ws.sent]
    assert tipos == ["tick"] * TICKS_PER_MINUTE + ["partido_finalizado"]
    assert ws.sent[0]["tiempoRestante"] == TICKS_PER_MINUTE - 1
    assert ws.sent[-2]["tiempoRestante"] == 0
    assert ws.sent[-1]["resultado"] == {"local": 0, "visitante": 0}


@pytest.mark.anyio
async def test_run_no_cierra_la_sala_de_inmediato_sino_tras_el_delay():
    ws = FakeWS()
    manager.rooms["match:f1"] = [ws]
    engine = _engine(match_id="f1")
    with patch.object(match_engine_module, "TICK_SECONDS", 0), \
         patch.object(match_engine_module, "ROOM_CLOSE_DELAY_SECONDS", 0.05), \
         patch.object(MatchEngine, "_persist_state"):
        await engine.run()
        assert ws.closed_with is None  # los espectadores todavía ven el resultado
        await asyncio.sleep(0.15)
    assert ws.closed_with == 1000
    assert "match:f1" not in manager.rooms


def test_el_delay_de_cierre_es_de_30_segundos():
    assert match_engine_module.ROOM_CLOSE_DELAY_SECONDS == 30


def test_la_sala_es_la_del_match_id():
    assert _engine(match_id="abc").room == "match:abc"
