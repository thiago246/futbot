import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.ws_manager import manager


def _register(client, email, club):
    client.post("/api/v1/auth/register", json={
        "username": email.split("@")[0], "email": email, "password": "12345678",
        "avatar": "x", "clubNombre": club})
    return client.post("/api/v1/auth/login", json={"email": email, "password": "12345678"}).json()["token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _league(client, token, min_teams=3, max_teams=4):
    r = client.post("/api/v1/leagues", headers=_h(token), json={
        "nombre": "Liga", "esPrivada": False, "minEquipos": min_teams,
        "maxEquipos": max_teams, "duracionPartido": 3})
    return r.json()["id"]


def _join(client, token, league_id):
    return client.post(f"/api/v1/leagues/{league_id}/join", headers=_h(token))


def _leave(client, token, league_id):
    return client.post(f"/api/v1/leagues/{league_id}/leave", headers=_h(token))


@pytest.fixture(autouse=True)
def clean_rooms():
    manager.rooms.clear()
    yield
    manager.rooms.clear()


@pytest.fixture()
def world(client):
    tokens = {n: _register(client, f"{n}@x.com", f"Club {n}") for n in "abcde"}
    return tokens, _league(client, tokens["a"])


# ---------- GET /leagues/{id}/lobby ----------

def test_get_lobby_empty(client, world):
    tokens, lid = world
    r = client.get(f"/api/v1/leagues/{lid}/lobby", headers=_h(tokens["a"]))
    assert r.status_code == 200
    body = r.json()
    assert body["equiposActuales"] == 1 and body["cuposRestantes"] == 3
    assert body["listaParaIniciar"] is False
    assert [e["nombre"] for e in body["equipos"]] == ["Club a"]


def test_get_lobby_lists_members_and_capacity(client, world):
    tokens, lid = world
    _join(client, tokens["b"], lid)
    body = client.get(f"/api/v1/leagues/{lid}/lobby", headers=_h(tokens["a"])).json()
    assert body["equiposActuales"] == 2 and body["cuposRestantes"] == 2
    assert [e["nombre"] for e in body["equipos"]] == ["Club a", "Club b"]
    assert body["minEquipos"] == 3 and body["maxEquipos"] == 4


def test_get_lobby_ready_flag_when_min_reached(client, world):
    tokens, lid = world
    for n in "bc":  # a ya está: con b y c son 3
        _join(client, tokens[n], lid)
    body = client.get(f"/api/v1/leagues/{lid}/lobby", headers=_h(tokens["a"])).json()
    assert body["listaParaIniciar"] is True


def test_get_lobby_not_found(client, world):
    tokens, _ = world
    r = client.get("/api/v1/leagues/00000000-0000-0000-0000-000000000000/lobby", headers=_h(tokens["a"]))
    assert r.status_code == 404 and r.json()["error"]["code"] == "LEAGUE_NOT_FOUND"


def test_get_lobby_unauthenticated(client, world):
    _, lid = world
    assert client.get(f"/api/v1/leagues/{lid}/lobby").status_code == 401


# ---------- WS /ws/leagues/{id}/lobby ----------

def test_ws_rejects_missing_token(client, world):
    _, lid = world
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(f"/ws/leagues/{lid}/lobby"):
            pass
    assert e.value.code == 4401


def test_ws_rejects_invalid_token(client, world):
    _, lid = world
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(f"/ws/leagues/{lid}/lobby?token=basura"):
            pass
    assert e.value.code == 4401


def test_ws_rejects_unknown_league(client, world):
    tokens, _ = world
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect(f"/ws/leagues/no-existe/lobby?token={tokens['a']}"):
            pass
    assert e.value.code == 4404


def test_ws_receives_equipo_unido_on_join(client, world):
    tokens, lid = world
    with client.websocket_connect(f"/ws/leagues/{lid}/lobby?token={tokens['a']}") as ws:
        assert _join(client, tokens["b"], lid).status_code == 200
        msg = ws.receive_json()
    assert msg["tipo"] == "equipo_unido"
    assert msg["clubNombre"] == "Club b"
    assert (msg["equiposActuales"], msg["maxEquipos"], msg["cuposRestantes"]) == (2, 4, 2)


def test_ws_receives_equipo_abandono_on_leave(client, world):
    tokens, lid = world
    _join(client, tokens["b"], lid)
    with client.websocket_connect(f"/ws/leagues/{lid}/lobby?token={tokens['a']}") as ws:
        assert _leave(client, tokens["b"], lid).status_code == 200
        msg = ws.receive_json()
    assert msg["tipo"] == "equipo_abandono" and msg["clubNombre"] == "Club b"
    assert msg["equiposActuales"] == 1 and msg["cuposRestantes"] == 3


def test_ws_ready_sent_when_min_reached_and_only_once(client, world):
    tokens, lid = world
    with client.websocket_connect(f"/ws/leagues/{lid}/lobby?token={tokens['a']}") as ws:
        for n in "bc":
            _join(client, tokens[n], lid)
        types = [ws.receive_json()["tipo"] for _ in range(3)]
    # b (2) -> unido | c (3, llega al mínimo) -> unido + lista
    assert types == ["equipo_unido", "equipo_unido", "liga_lista_para_iniciar"]


def test_ws_no_ready_if_min_already_reached(client, world):
    tokens, lid = world
    for n in "bc":  # con a son 3: el mínimo ya estaba
        _join(client, tokens[n], lid)
    with client.websocket_connect(f"/ws/leagues/{lid}/lobby?token={tokens['a']}") as ws:
        _join(client, tokens["d"], lid)  # 4to club
        assert ws.receive_json()["tipo"] == "equipo_unido"
        _leave(client, tokens["d"], lid)
        assert ws.receive_json()["tipo"] == "equipo_abandono"  # nada de "lista" en el medio


def test_ws_ready_sent_again_after_leave_and_rejoin(client, world):
    tokens, lid = world
    _join(client, tokens["b"], lid)  # con a son 2
    with client.websocket_connect(f"/ws/leagues/{lid}/lobby?token={tokens['a']}") as ws:
        _join(client, tokens["c"], lid)
        assert [ws.receive_json()["tipo"] for _ in range(2)] == ["equipo_unido", "liga_lista_para_iniciar"]
        _leave(client, tokens["c"], lid)
        assert ws.receive_json()["tipo"] == "equipo_abandono"
        _join(client, tokens["c"], lid)
        assert [ws.receive_json()["tipo"] for _ in range(2)] == ["equipo_unido", "liga_lista_para_iniciar"]


def test_ws_all_connected_clients_get_the_event(client, world):
    tokens, lid = world
    with client.websocket_connect(f"/ws/leagues/{lid}/lobby?token={tokens['a']}") as w1, \
         client.websocket_connect(f"/ws/leagues/{lid}/lobby?token={tokens['c']}") as w2:
        _join(client, tokens["b"], lid)
        assert w1.receive_json()["tipo"] == "equipo_unido"
        assert w2.receive_json()["tipo"] == "equipo_unido"


def test_ws_failed_join_emits_nothing(client, world):
    tokens, lid = world
    _join(client, tokens["b"], lid)
    with client.websocket_connect(f"/ws/leagues/{lid}/lobby?token={tokens['a']}") as ws:
        assert _join(client, tokens["b"], lid).status_code == 409  # ya inscripto
        _join(client, tokens["c"], lid)  # este sí emite
        msg = ws.receive_json()
    assert msg["clubNombre"] == "Club c"  # el primer mensaje es del join válido, no del fallido


def test_ws_room_is_cleaned_after_disconnect(client, world):
    tokens, lid = world
    with client.websocket_connect(f"/ws/leagues/{lid}/lobby?token={tokens['a']}"):
        assert f"league:{lid}" in manager.rooms
    assert f"league:{lid}" not in manager.rooms


def test_ws_list_receives_update_on_join_and_leave(client, world):
    tokens, lid = world
    with client.websocket_connect(f"/ws/leagues?token={tokens['a']}") as ws:
        _join(client, tokens["b"], lid)
        msg = ws.receive_json()
        assert msg["tipo"] == "liga_actualizada" and msg["equiposActuales"] == 2
        _leave(client, tokens["b"], lid)
        assert ws.receive_json()["equiposActuales"] == 1


def test_ws_list_receives_new_league(client, world):
    tokens, _ = world
    with client.websocket_connect(f"/ws/leagues?token={tokens['a']}") as ws:
        _league(client, tokens["b"])
        assert ws.receive_json()["tipo"] == "liga_creada"

def test_ws_list_rejects_missing_token(client, world):
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect("/ws/leagues"):
            pass
    assert e.value.code == 4401


def test_ws_list_rejects_invalid_token(client, world):
    with pytest.raises(WebSocketDisconnect) as e:
        with client.websocket_connect("/ws/leagues?token=basura"):
            pass
    assert e.value.code == 4401


def test_ws_list_receives_new_league_with_payload(client, world):
    tokens, _ = world
    with client.websocket_connect(f"/ws/leagues?token={tokens['a']}") as ws:
        _league(client, tokens["b"])
        msg = ws.receive_json()
    assert msg["tipo"] == "liga_creada"
    assert msg["liga"]["nombre"] == "Liga"
    assert msg["liga"]["equiposActuales"] == 1   # el creador ya está inscripto
    assert msg["total"] == 2


def test_ws_list_update_when_league_fills_and_reopens(client, world):
    tokens, lid = world  # maxEquipos = 4, a ya está
    with client.websocket_connect(f"/ws/leagues?token={tokens['a']}") as ws:
        for n in "bcd":
            _join(client, tokens[n], lid)
        msgs = [ws.receive_json() for _ in range(3)]
        assert msgs[-1]["equiposActuales"] == 4
        assert msgs[-1]["estado"] == "en_curso"
        _leave(client, tokens["d"], lid)
        msg = ws.receive_json()
    assert msg["equiposActuales"] == 3
    assert msg["estado"] == "esperando_equipos"


def test_ws_list_failed_join_emits_nothing(client, world):
    tokens, lid = world
    _join(client, tokens["b"], lid)
    with client.websocket_connect(f"/ws/leagues?token={tokens['a']}") as ws:
        assert _join(client, tokens["b"], lid).status_code == 409  # ya inscripto
        _join(client, tokens["c"], lid)
        msg = ws.receive_json()
    # el primer mensaje es el del join válido de c, no el del fallido de b
    assert msg["equiposActuales"] == 3


def test_ws_list_all_connected_clients_get_the_event(client, world):
    tokens, lid = world
    with client.websocket_connect(f"/ws/leagues?token={tokens['a']}") as w1, \
         client.websocket_connect(f"/ws/leagues?token={tokens['c']}") as w2:
        _join(client, tokens["b"], lid)
        assert w1.receive_json()["tipo"] == "liga_actualizada"
        assert w2.receive_json()["tipo"] == "liga_actualizada"


def test_ws_list_room_is_cleaned_after_disconnect(client, world):
    tokens, _ = world
    with client.websocket_connect(f"/ws/leagues?token={tokens['a']}"):
        assert "leagues:list" in manager.rooms
    assert "leagues:list" not in manager.rooms

def test_get_leagues_includes_member_count(client, world):
    tokens, lid = world
    _join(client, tokens["b"], lid)
    _join(client, tokens["c"], lid)
    body = client.get("/api/v1/leagues", headers=_h(tokens["a"])).json()
    assert body["items"][0]["equiposActuales"] == 3