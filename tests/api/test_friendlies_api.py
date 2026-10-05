"""Tests de API de amistosos.

Por ahora solo Crear amistoso (POST /matches).
Las claves del JSON (duracion, clubLocalId, ...) son las del contrato, en español.
"""
from datetime import datetime, timedelta

import pytest

from app.models.behavior import Behavior
from app.models.club_player import ClubPlayer
from app.models.friendly import Friendly
from app.models.squads import FriendlySquadMember, Squad, SquadMember
from app.services import friendly_service

CREATOR_PAYLOAD = {
    "username": "creator",
    "email": "creator@example.com",
    "password": "12345678",
    "avatar": "1",
    "clubNombre": "creator club",
}


RIVAL_PAYLOAD = {
    "username": "rival",
    "email": "rival@example.com",
    "password": "12345678",
    "avatar": "1",
    "clubNombre": "rival club",
}


def _register(client, payload=CREATOR_PAYLOAD):
    """Registra un usuario y devuelve (headers con token, id del club)."""
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201
    body = r.json()
    return {"Authorization": f"Bearer {body['token']}"}, body["club"]["id"]


def _create_default_squad(db_session, club_id):
    """Inserta directo en la DB una plantilla válida para el club."""
    # 6 comportamientos distintos: un club no puede repetir uno en su plantilla.
    # Se reutilizan entre clubes: clubes distintos sí pueden usar el mismo.
    behaviors = []
    for i in range(6):
        behavior = db_session.query(Behavior).filter_by(name=f"test-behavior-{i}").first()
        if behavior is None:
            behavior = Behavior(name=f"test-behavior-{i}", code="pass", is_default=False)
            db_session.add(behavior)
            db_session.flush()
        behaviors.append(behavior)

    players = [
        ClubPlayer(
            name=f"Player {i}", strength=60, control=60, precision=60,
            agility=60, speed=60, club_id=club_id,
        )
        for i in range(6)
    ]
    db_session.add_all(players)
    db_session.flush()

    squad = Squad(club_id=club_id, formation="1-2")
    db_session.add(squad)
    db_session.flush()

    for i, player in enumerate(players):
        db_session.add(SquadMember(
            squad_id=squad.id,
            club_player_id=player.id,
            behavior_id=behaviors[i].id,
            is_starter=i < 3,
        ))
    db_session.commit()


@pytest.fixture(autouse=True)
def countdown(monkeypatch):
    """Unirse agenda run_countdown con BackgroundTasks, y el TestClient espera a que
    terminen: sin esto cada join exitoso tardaría 15 s y el partido terminaría en
    "en_curso" (y la tarea abriría la DB real, no la de los tests).
    Devuelve la lista de partidos cuya cuenta regresiva se agendó."""
    scheduled = []

    async def fake_run_countdown(friendly_id):
        scheduled.append(friendly_id)

    monkeypatch.setattr(friendly_service, "run_countdown", fake_run_countdown)
    return scheduled


def test_create_friendly_invalid_token(client):
    response = client.post(
        "/api/v1/matches",
        json={"duracion": 3},
        headers={"Authorization": "Bearer basura"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_create_friendly_success(client, db_session):
    headers, club_id = _register(client)
    _create_default_squad(db_session, club_id)

    response = client.post("/api/v1/matches", json={"duracion": 3}, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["tipo"] == "amistoso"
    assert body["estado"] == "esperando_rival"
    assert body["clubLocalId"] == club_id
    assert body["clubVisitanteId"] is None
    assert body["duracion"] == 3
    assert body["resultadoLocal"] == 0
    assert body["resultadoVisitante"] == 0
    assert body["sustitucionesRestantes"] == 3


def test_create_friendly_is_saved(client, db_session):
    headers, club_id = _register(client)
    _create_default_squad(db_session, club_id)

    response = client.post("/api/v1/matches", json={"duracion": 5}, headers=headers)

    saved = db_session.get(Friendly, response.json()["id"])
    assert saved is not None
    assert saved.home_club_id == club_id
    assert saved.status == "esperando_rival"


@pytest.mark.parametrize("duration", [1, 3, 5])
def test_create_friendly_valid_durations(client, db_session, duration):
    headers, club_id = _register(client)
    _create_default_squad(db_session, club_id)

    response = client.post("/api/v1/matches", json={"duracion": duration}, headers=headers)

    assert response.status_code == 201
    assert response.json()["duracion"] == duration


@pytest.mark.parametrize("duration", [0, 2, 4, 10])
def test_create_friendly_invalid_duration(client, db_session, duration):
    headers, club_id = _register(client)
    _create_default_squad(db_session, club_id)

    response = client.post("/api/v1/matches", json={"duracion": duration}, headers=headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DURATION"


def test_create_friendly_without_squad(client, db_session):
    headers, _ = _register(client)

    response = client.post("/api/v1/matches", json={"duracion": 3}, headers=headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SQUAD_NOT_CONFIGURED"
    assert db_session.query(Friendly).count() == 0


def test_create_friendly_without_duration(client):
    headers, _ = _register(client)

    response = client.post("/api/v1/matches", json={}, headers=headers)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Listar amistosos (GET /matches)
# ---------------------------------------------------------------------------
T0 = datetime(2026, 1, 1, 12, 0, 0)


def _insert_friendly(db_session, status="esperando_rival", kind="amistoso", minutes=0,
                     home_club_id="club-x", away_club_id=None):
    """Inserta directo un Friendly; `minutes` desplaza created_at para controlar el orden."""
    friendly = Friendly(
        kind=kind,
        status=status,
        home_club_id=home_club_id,  # SQLite en memoria no valida la FK
        away_club_id=away_club_id,
        duration=3,
        created_at=T0 + timedelta(minutes=minutes),
    )
    db_session.add(friendly)
    db_session.commit()
    db_session.refresh(friendly)
    return friendly


def test_list_friendlies_invalid_token(client):
    response = client.get("/api/v1/matches", headers={"Authorization": "Bearer basura"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_list_friendlies_filters_by_status_and_kind(client, db_session):
    headers, _ = _register(client)
    waiting = _insert_friendly(db_session, "esperando_rival", "amistoso", minutes=0)
    _insert_friendly(db_session, "en_curso", "amistoso", minutes=1)
    _insert_friendly(db_session, "esperando_rival", "liga", minutes=2)

    response = client.get("/api/v1/matches?estado=esperando_rival&tipo=amistoso", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["items"]] == [waiting.id]
    assert all(item["estado"] == "esperando_rival" for item in body["items"])
    assert all(item["tipo"] == "amistoso" for item in body["items"])
    assert body["total"] == 1


def test_list_friendlies_only_requested_status(client, db_session):
    headers, _ = _register(client)
    _insert_friendly(db_session, "esperando_rival", minutes=0)
    _insert_friendly(db_session, "programado", minutes=1)
    _insert_friendly(db_session, "en_curso", minutes=2)

    response = client.get("/api/v1/matches?estado=programado", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["estado"] == "programado"


def test_list_friendlies_response_format(client, db_session):
    headers, _ = _register(client)
    _insert_friendly(db_session)

    response = client.get("/api/v1/matches", headers=headers)

    body = response.json()
    assert set(body) == {"items", "page", "pageSize", "total"}
    assert body["page"] == 1
    assert body["pageSize"] == 20
    assert set(body["items"][0]) == {
        "id", "tipo", "estado", "clubLocalId", "clubVisitanteId",
        "resultadoLocal", "resultadoVisitante", "duracion", "sustitucionesRestantes",
    }


def test_list_friendlies_includes_own_club_friendlies(client, db_session):
    headers, club_id = _register(client)
    own = _insert_friendly(db_session, home_club_id=club_id, minutes=0)
    _insert_friendly(db_session, home_club_id="otro-club", minutes=1)

    response = client.get("/api/v1/matches?estado=esperando_rival", headers=headers)

    items = response.json()["items"]
    assert len(items) == 2
    assert own.id in [item["id"] for item in items]


def test_list_friendlies_orders_oldest_first(client, db_session):
    headers, _ = _register(client)
    newest = _insert_friendly(db_session, minutes=10)
    oldest = _insert_friendly(db_session, minutes=0)
    middle = _insert_friendly(db_session, minutes=5)

    response = client.get("/api/v1/matches", headers=headers)

    assert [item["id"] for item in response.json()["items"]] == [oldest.id, middle.id, newest.id]


def test_list_friendlies_paginates(client, db_session):
    headers, _ = _register(client)
    created = [_insert_friendly(db_session, minutes=i) for i in range(5)]

    response = client.get("/api/v1/matches?page=2&pageSize=2", headers=headers)

    body = response.json()
    assert [item["id"] for item in body["items"]] == [created[2].id, created[3].id]
    assert body["page"] == 2
    assert body["pageSize"] == 2
    assert body["total"] == 5


def test_list_friendlies_empty(client):
    headers, _ = _register(client)

    response = client.get("/api/v1/matches", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"items": [], "page": 1, "pageSize": 20, "total": 0}


def test_list_friendlies_kind_liga_returns_empty_list(client, db_session):
    headers, _ = _register(client)
    _insert_friendly(db_session, kind="amistoso")

    response = client.get("/api/v1/matches?tipo=liga", headers=headers)

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


@pytest.mark.parametrize(
    "status",
    ["esperando_rival", "programado", "cuenta_regresiva", "en_curso", "pausado", "finalizado"],
)
def test_list_friendlies_accepts_every_contract_status(client, status):
    headers, _ = _register(client)

    response = client.get(f"/api/v1/matches?estado={status}", headers=headers)

    assert response.status_code == 200


@pytest.mark.parametrize(
    "query",
    ["estado=inventado", "tipo=inventado", "page=0", "page=-1", "pageSize=0", "pageSize=101"],
)
def test_list_friendlies_rejects_invalid_params(client, query):
    headers, _ = _register(client)

    response = client.get(f"/api/v1/matches?{query}", headers=headers)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Unirse a amistoso (POST /matches/{matchId}/join)
# ---------------------------------------------------------------------------
UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"


def _join(client, headers, match_id):
    return client.post(f"/api/v1/matches/{match_id}/join", headers=headers)


def test_join_friendly_invalid_token(client):
    response = _join(client, {"Authorization": "Bearer basura"}, UNKNOWN_ID)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_join_friendly_success(client, db_session, countdown):
    _, home_club_id = _register(client)
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, home_club_id)
    _create_default_squad(db_session, rival_club_id)
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    response = _join(client, rival_headers, friendly.id)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == friendly.id
    assert body["clubLocalId"] == home_club_id
    assert body["clubVisitanteId"] == rival_club_id
    assert body["estado"] == "cuenta_regresiva"
    assert countdown == [friendly.id]


def test_join_friendly_is_saved(client, db_session):
    _, home_club_id = _register(client)
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, home_club_id)
    _create_default_squad(db_session, rival_club_id)
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    _join(client, rival_headers, friendly.id)

    db_session.expire_all()
    saved = db_session.get(Friendly, friendly.id)
    assert saved.away_club_id == rival_club_id
    assert saved.status == "cuenta_regresiva"


def test_join_friendly_own_match(client, db_session):
    home_headers, home_club_id = _register(client)
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    response = _join(client, home_headers, friendly.id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CANNOT_JOIN_OWN_MATCH"
    db_session.refresh(friendly)
    assert friendly.away_club_id is None


def test_join_friendly_match_full(client, db_session):
    _, home_club_id = _register(client)
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, rival_club_id)
    friendly = _insert_friendly(
        db_session, status="programado", home_club_id=home_club_id, away_club_id="otro-club"
    )

    response = _join(client, rival_headers, friendly.id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MATCH_FULL"
    db_session.refresh(friendly)
    assert friendly.away_club_id == "otro-club"


def test_join_friendly_twice_is_rejected(client, db_session):
    _, home_club_id = _register(client)
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, home_club_id)
    _create_default_squad(db_session, rival_club_id)
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    first = _join(client, rival_headers, friendly.id)
    second = _join(client, rival_headers, friendly.id)

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "MATCH_FULL"


@pytest.mark.parametrize("status", ["cuenta_regresiva", "en_curso", "pausado", "finalizado"])
def test_join_friendly_match_not_available(client, db_session, status):
    _, home_club_id = _register(client)
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, rival_club_id)
    friendly = _insert_friendly(db_session, status=status, home_club_id=home_club_id)

    response = _join(client, rival_headers, friendly.id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MATCH_NOT_AVAILABLE"


def test_join_friendly_without_squad(client, db_session):
    _, home_club_id = _register(client)
    rival_headers, _ = _register(client, RIVAL_PAYLOAD)
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    response = _join(client, rival_headers, friendly.id)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SQUAD_NOT_CONFIGURED"
    db_session.refresh(friendly)
    assert friendly.away_club_id is None
    assert friendly.status == "esperando_rival"


def test_join_friendly_unknown_match(client, db_session):
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, rival_club_id)

    response = _join(client, rival_headers, UNKNOWN_ID)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MATCH_NOT_FOUND"


def test_join_friendly_removes_it_from_the_waiting_list(client, db_session):
    _, home_club_id = _register(client)
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, home_club_id)
    _create_default_squad(db_session, rival_club_id)
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    _join(client, rival_headers, friendly.id)

    waiting = client.get("/api/v1/matches?estado=esperando_rival", headers=rival_headers).json()
    counting_down = client.get("/api/v1/matches?estado=cuenta_regresiva", headers=rival_headers).json()
    assert waiting["items"] == []
    assert [item["id"] for item in counting_down["items"]] == [friendly.id]

# ---------------------------------------------------------------------------
# Inicio automático al unirse: plantillas congeladas y cuenta regresiva
# ---------------------------------------------------------------------------
THIRD_PAYLOAD = {
    "username": "third",
    "email": "third@example.com",
    "password": "12345678",
    "avatar": "1",
    "clubNombre": "third club",
}

FOURTH_PAYLOAD = {
    "username": "fourth",
    "email": "fourth@example.com",
    "password": "12345678",
    "avatar": "1",
    "clubNombre": "fourth club",
}


def _snapshot_count(db_session, friendly_id):
    return db_session.query(FriendlySquadMember).filter_by(friendly_id=friendly_id).count()


def test_join_friendly_freezes_both_squads(client, db_session):
    _, home_club_id = _register(client)
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, home_club_id)
    _create_default_squad(db_session, rival_club_id)
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    _join(client, rival_headers, friendly.id)

    db_session.expire_all()
    assert _snapshot_count(db_session, friendly.id) == 12


def test_join_friendly_rejected_does_not_start_anything(client, db_session, countdown):
    home_headers, home_club_id = _register(client)
    _create_default_squad(db_session, home_club_id)
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    response = _join(client, home_headers, friendly.id)  # su propio partido

    assert response.status_code == 409
    assert countdown == []
    assert _snapshot_count(db_session, friendly.id) == 0


def test_join_friendly_twice_schedules_a_single_countdown(client, db_session, countdown):
    _, home_club_id = _register(client)
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, home_club_id)
    _create_default_squad(db_session, rival_club_id)
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    _join(client, rival_headers, friendly.id)
    _join(client, rival_headers, friendly.id)

    assert countdown == [friendly.id]
    assert _snapshot_count(db_session, friendly.id) == 12


def test_join_friendly_when_home_club_has_no_squad(client, db_session, countdown):
    """El local pudo perder/no tener plantilla desde que publicó el amistoso."""
    _, home_club_id = _register(client)
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, rival_club_id)
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    response = _join(client, rival_headers, friendly.id)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SQUAD_NOT_CONFIGURED"
    db_session.refresh(friendly)
    assert friendly.away_club_id is None
    assert friendly.status == "esperando_rival"
    assert countdown == []


def test_join_friendly_when_a_club_repeats_a_behavior(client, db_session, countdown):
    """Un comportamiento puede usarse en varios partidos, pero un mismo club no
    puede usarlo dos veces dentro del mismo partido."""
    _, home_club_id = _register(client)
    rival_headers, rival_club_id = _register(client, RIVAL_PAYLOAD)
    _create_default_squad(db_session, home_club_id)
    _create_default_squad(db_session, rival_club_id)
    members = (
        db_session.query(SquadMember)
        .join(Squad, SquadMember.squad_id == Squad.id)
        .filter(Squad.club_id == rival_club_id)
        .order_by(SquadMember.id)
        .all()
    )
    members[1].behavior_id = members[0].behavior_id
    db_session.commit()
    friendly = _insert_friendly(db_session, home_club_id=home_club_id)

    response = _join(client, rival_headers, friendly.id)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "BEHAVIOR_IN_USE"
    db_session.refresh(friendly)
    assert friendly.away_club_id is None
    assert friendly.status == "esperando_rival"
    assert countdown == []


def test_join_friendly_allows_simultaneous_matches_sharing_behaviors(client, db_session, countdown):
    """Cuatro clubes con los mismos 6 comportamientos, dos partidos a la vez."""
    _, first_home = _register(client)
    first_rival_headers, first_rival = _register(client, RIVAL_PAYLOAD)
    _, second_home = _register(client, THIRD_PAYLOAD)
    second_rival_headers, second_rival = _register(client, FOURTH_PAYLOAD)
    for club_id in (first_home, first_rival, second_home, second_rival):
        _create_default_squad(db_session, club_id)
    first = _insert_friendly(db_session, home_club_id=first_home, minutes=0)
    second = _insert_friendly(db_session, home_club_id=second_home, minutes=1)

    first_response = _join(client, first_rival_headers, first.id)
    second_response = _join(client, second_rival_headers, second.id)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert countdown == [first.id, second.id]