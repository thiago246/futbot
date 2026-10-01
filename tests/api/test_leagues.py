from app.core.exceptions import (MatchDurationNotAllowed, MinTeamsTooLowError, 
                                EmptyLeaguePasswordError, InvalidLeaguePasswordError, 
                                AlreadyInLeagueError, LeagueNotFoundError, NotInLeagueError)

def _register_and_login(client, email="join@example.com", password="12345678"):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "thiago",
            "email": email,
            "password": password,
            "avatar": "hola",
            "clubNombre": "los thiagos",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return response.json()["token"]

def _create_public_league(client, token):
    response = client.post(
        "/api/v1/leagues",
        json={
            "nombre": "Liga Publica",
            "esPrivada": False,
            "minEquipos": 3,
            "maxEquipos": 4,
            "duracionPartido": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()["id"]


def _create_private_league(client, token, password="secreto123"):
    response = client.post(
        "/api/v1/leagues",
        json={
            "nombre": "Liga Privada",
            "esPrivada": True,
            "password": password,
            "minEquipos": 3,
            "maxEquipos": 4,
            "duracionPartido": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()["id"]



def test_create_public_league_success(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/v1/leagues",
        json={
            "nombre": "Liga Publica",
            "esPrivada": False,
            "minEquipos": 3,
            "maxEquipos": 8,
            "duracionPartido": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["nombre"] == "Liga Publica"
    assert body["esPrivada"] == False
    assert body["estado"] == "esperando_equipos"
    assert "id" in body


def test_create_private_league_success(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/v1/leagues",
        json={
            "nombre": "Liga Privada",
            "esPrivada": True,
            "password": "secreto123",
            "minEquipos": 3,
            "maxEquipos": 6,
            "duracionPartido": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["esPrivada"] == True
    assert "password" not in body


def test_create_league_min_teams_too_low(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/v1/leagues",
        json={
            "nombre": "Liga Invalida",
            "esPrivada": False,
            "minEquipos": 2,
            "maxEquipos": 8,
            "duracionPartido": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert MinTeamsTooLowError


def test_create_private_league_without_password(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/v1/leagues",
        json={
            "nombre": "Liga Sin Pass",
            "esPrivada": True,
            "minEquipos": 3,
            "maxEquipos": 8,
            "duracionPartido": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert EmptyLeaguePasswordError


def test_create_league_invalid_duration(client):
    token = _register_and_login(client, email="invalid_duration@example.com")

    response = client.post(
        "/api/v1/leagues",
        json={
            "nombre": "Liga Duracion Invalida",
            "esPrivada": False,
            "minEquipos": 3,
            "maxEquipos": 8,
            "duracionPartido": 2,  # only 1, 3, 5 are valid
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    print(response.json())
    assert response.status_code == 422
    assert MatchDurationNotAllowed


def test_create_league_unauthenticated(client):
    response = client.post(
        "/api/v1/leagues",
        json={
            "nombre": "Liga Sin Auth",
            "esPrivada": False,
            "minEquipos": 3,
            "maxEquipos": 8,
            "duracionPartido": 3,
        },
    )

    assert response.status_code == 401


def test_list_leagues_empty(client):
    token = _register_and_login(client)

    response = client.get(
        "/api/v1/leagues",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 1


def test_list_leagues_returns_created(client):
    token = _register_and_login(client)

    client.post(
        "/api/v1/leagues",
        json={
            "nombre": "Liga Publica",
            "esPrivada": False,
            "minEquipos": 3,
            "maxEquipos": 8,
            "duracionPartido": 3,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/api/v1/leagues",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["nombre"] == "Liga Publica"

def test_list_leagues_pagination(client):
    token = _register_and_login(client)

    for i in range(5):
        client.post(
            "/api/v1/leagues",
            json={
                "nombre": f"Liga {i}",
                "esPrivada": False,
                "minEquipos": 3,
                "maxEquipos": 8,
                "duracionPartido": 3,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    response = client.get(
        "/api/v1/leagues?page=1&pageSize=3",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 3
    assert body["page"] == 1
    assert body["pageSize"] == 3

def test_join_public_league_success(client):
    token_a = _register_and_login(client, email="a@example.com")
    token_b = _register_and_login(client, email="b@example.com")
    league_id = _create_public_league(client, token_a)

    response = client.post(
        f"/api/v1/leagues/{league_id}/join",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 200


def test_join_private_league_success(client):
    token_a = _register_and_login(client, email="a@example.com")
    token_b = _register_and_login(client, email="b@example.com")
    league_id = _create_private_league(client, token_a, password="secreto123")

    response = client.post(
        f"/api/v1/leagues/{league_id}/join",
        json={"password": "secreto123"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 200


def test_join_private_league_wrong_password(client):
    token_a = _register_and_login(client, email="a@example.com")
    token_b = _register_and_login(client, email="b@example.com")
    league_id = _create_private_league(client, token_a, password="secreto123")

    response = client.post(
        f"/api/v1/leagues/{league_id}/join",
        json={"password": "incorrecta"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 401
    assert InvalidLeaguePasswordError


def test_join_league_already_member(client):
    token_a = _register_and_login(client, email="a@example.com")
    token_b = _register_and_login(client, email="b@example.com")
    league_id = _create_public_league(client, token_a)

    client.post(
        f"/api/v1/leagues/{league_id}/join",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    response = client.post(
        f"/api/v1/leagues/{league_id}/join",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 409
    assert AlreadyInLeagueError

def test_join_league_not_found(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/v1/leagues/00000000-0000-0000-0000-000000000000/join",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert LeagueNotFoundError


def test_join_league_unauthenticated(client):
    token = _register_and_login(client)
    league_id = _create_public_league(client, token)

    response = client.post(f"/api/v1/leagues/{league_id}/join")

    assert response.status_code == 401


def test_join_started_league(client):
    token_a = _register_and_login(client, email="a@example.com")
    token_b = _register_and_login(client, email="b@example.com")
    token_c = _register_and_login(client, email="c@example.com")
    token_d = _register_and_login(client, email="d@example.com")
    token_e = _register_and_login(client, email="e@example.com")

    league_id = _create_public_league(client, token_a)

    # llenar la liga completa (max_teams=4): b, c, d, y el propio a
    for token in [token_a, token_b, token_c, token_d]:
        client.post(
            f"/api/v1/leagues/{league_id}/join",
            headers={"Authorization": f"Bearer {token}"},
        )

    # ahora la liga está en_curso, token_e no puede unirse
    response = client.post(
        f"/api/v1/leagues/{league_id}/join",
        headers={"Authorization": f"Bearer {token_e}"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "LEAGUE_ALREADY_STARTED"

def test_leave_league_success(client):
    token_a = _register_and_login(client, email="a@example.com")
    token_b = _register_and_login(client, email="b@example.com")
    league_id = _create_public_league(client, token_a)

    client.post(
        f"/api/v1/leagues/{league_id}/join",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    response = client.post(
        f"/api/v1/leagues/{league_id}/leave",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 200


def test_leave_league_not_member(client):
    token_a = _register_and_login(client, email="a@example.com")
    token_b = _register_and_login(client, email="b@example.com")
    league_id = _create_public_league(client, token_a)

    response = client.post(
        f"/api/v1/leagues/{league_id}/leave",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 404
    assert NotInLeagueError


def test_leave_league_not_found(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/v1/leagues/00000000-0000-0000-0000-000000000000/leave",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert LeagueNotFoundError


def test_leave_league_unauthenticated(client):
    token = _register_and_login(client)
    league_id = _create_public_league(client, token)

    response = client.post(f"/api/v1/leagues/{league_id}/leave")

    assert response.status_code == 401


def test_leave_league_restores_status_to_waiting(client):
    token_a = _register_and_login(client, email="a@example.com")
    token_b = _register_and_login(client, email="b@example.com")
    token_c = _register_and_login(client, email="c@example.com")
    token_d = _register_and_login(client, email="d@example.com")
    league_id = _create_public_league(client, token_a)

    # fill the league (max_teams=4) so it goes to en_curso
    for token in [token_a, token_b, token_c, token_d]:
        client.post(
            f"/api/v1/leagues/{league_id}/join",
            headers={"Authorization": f"Bearer {token}"},
        )

    # token_d leaves, league should go back to esperando_equipos
    client.post(
        f"/api/v1/leagues/{league_id}/leave",
        headers={"Authorization": f"Bearer {token_d}"},
    )

    response = client.get(
        f"/api/v1/leagues/{league_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response.status_code == 200
    assert response.json()["estado"] == "esperando_equipos"


def test_leave_league_allows_rejoin(client):
    token_a = _register_and_login(client, email="a@example.com")
    token_b = _register_and_login(client, email="b@example.com")
    league_id = _create_public_league(client, token_a)

    client.post(
        f"/api/v1/leagues/{league_id}/join",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    client.post(
        f"/api/v1/leagues/{league_id}/leave",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    response = client.post(
        f"/api/v1/leagues/{league_id}/join",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 200