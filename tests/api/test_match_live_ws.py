"""WS /ws/matches/{matchId}/live: autenticación, partido inexistente/finalizado y sala.

La emisión de tick / partido_finalizado se prueba en tests/unit/test_live_channel.py.
El matchId es el Match.id (para amistosos coincide con el id del Friendly).
"""
import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.ws_manager import manager
from app.models.friendly import Friendly
from app.models.match import Match


def _register(client, email, club):
    client.post("/api/v1/auth/register", json={
        "username": email.split("@")[0], "email": email, "password": "12345678",
        "avatar": "x", "clubNombre": club})
    return client.post("/api/v1/auth/login", json={"email": email, "password": "12345678"}).json()["token"]


def _add_friendly(db, status="cuenta_regresiva") -> str:
    friendly = Friendly(home_club_id="club-fake", away_club_id="club-fake-2", duration=1, status=status)
    db.add(friendly)
    db.commit()
    return friendly.id


def _add_match(db, match_id, status="in_progress") -> None:
    db.add(Match(id=match_id, friendly_id=match_id, status=status))
    db.commit()


def _connect(client, match_id, token):
    return client.websocket_connect(f"/ws/matches/{match_id}/live?token={token}")


@pytest.fixture(autouse=True)
def clean_rooms():
    manager.rooms.clear()
    yield
    manager.rooms.clear()


@pytest.fixture()
def world(client, db_session):
    token = _register(client, "a@x.com", "Club a")
    return token, _add_friendly(db_session)


# ---------- rechazos ----------

def test_ws_rejects_missing_token(client, world):
    _, mid = world
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(f"/ws/matches/{mid}/live"):
            pass
    assert e.value.code == 4401


def test_ws_rejects_invalid_token(client, world):
    _, mid = world
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(f"/ws/matches/{mid}/live?token=basura"):
            pass
    assert e.value.code == 4401


def test_ws_rejects_unknown_match(client, world):
    token, _ = world
    with pytest.raises(WebSocketDisconnect) as e:
        with _connect(client, "00000000-0000-0000-0000-000000000000", token):
            pass
    assert e.value.code == 4404


def test_ws_rejects_finished_match(client, db_session, world):
    token, mid = world
    _add_match(db_session, mid, status="finished")
    with pytest.raises(WebSocketDisconnect) as e:
        with _connect(client, mid, token):
            pass
    assert e.value.code == 4404
    assert f"match:{mid}" not in manager.rooms


def test_ws_rejects_finalized_friendly_without_match_row(client, db_session):
    token = _register(client, "a@x.com", "Club a")
    mid = _add_friendly(db_session, status="finalizado")
    with pytest.raises(WebSocketDisconnect) as e:
        with _connect(client, mid, token):
            pass
    assert e.value.code == 4404


# ---------- conexiones válidas ----------

def test_ws_accepts_during_countdown_before_match_row_exists(client, world):
    token, mid = world  # amistoso en cuenta_regresiva, todavía sin fila Match
    with _connect(client, mid, token):
        assert len(manager.rooms[f"match:{mid}"]) == 1


def test_ws_accepts_match_in_progress(client, db_session, world):
    token, mid = world
    _add_match(db_session, mid, status="in_progress")
    with _connect(client, mid, token):
        assert f"match:{mid}" in manager.rooms


def test_ws_any_authenticated_user_can_watch(client, world):
    _, mid = world
    other = _register(client, "b@x.com", "Club b")
    with _connect(client, mid, other):
        assert f"match:{mid}" in manager.rooms


def test_ws_all_connections_share_the_room(client, world):
    token, mid = world
    other = _register(client, "b@x.com", "Club b")
    with _connect(client, mid, token), _connect(client, mid, other):
        assert len(manager.rooms[f"match:{mid}"]) == 2


def test_ws_room_is_cleaned_after_disconnect(client, world):
    token, mid = world
    with _connect(client, mid, token):
        assert f"match:{mid}" in manager.rooms
    assert f"match:{mid}" not in manager.rooms
