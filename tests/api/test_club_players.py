from app.core.exceptions import AttributeOutOfRangeError, AttributeSumInvalidError


def _register_and_login(client, email="player@example.com", password="12345678"):
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


def test_create_player_success(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/v1/clubs/me/players",
        json={
            "name": "nine",
            "stats": {
                "strength": 60,
                "control": 60,
                "precision": 60,
                "agility": 60,
                "speed": 60,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "nine"
    assert body["stats"]["strength"] == 60
    assert "id" in body


def test_create_player_stat_out_of_range(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/v1/clubs/me/players",
        json={
            "name": "nine",
            "stats": {
                "strength": 10,  # below 20
                "control": 60,
                "precision": 60,
                "agility": 60,
                "speed": 60,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert AttributeOutOfRangeError


def test_create_player_stat_sum_invalid(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/v1/clubs/me/players",
        json={
            "name": "nine",
            "stats": {
                "strength": 20,
                "control": 20,
                "precision": 20,
                "agility": 20,
                "speed": 20,  # sum = 100, not 300
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert AttributeSumInvalidError


def test_create_player_missing_fields(client):
    token = _register_and_login(client)

    response = client.post(
        "/api/v1/clubs/me/players",
        json={"name": "nine"},  # missing stats
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_create_player_unauthenticated(client):
    response = client.post(
        "/api/v1/clubs/me/players",
        json={
            "name": "nine",
            "stats": {
                "strength": 60,
                "control": 60,
                "precision": 60,
                "agility": 60,
                "speed": 60,
            },
        },
    )

    assert response.status_code == 401


def test_list_players_empty(client):
    token = _register_and_login(client)

    response = client.get(
        "/api/v1/clubs/me/players",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_players_returns_created(client):
    token = _register_and_login(client)

    client.post(
        "/api/v1/clubs/me/players",
        json={
            "name": "nine",
            "stats": {
                "strength": 60,
                "control": 60,
                "precision": 60,
                "agility": 60,
                "speed": 60,
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/api/v1/clubs/me/players",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "nine"


def test_list_players_only_own_club(client):
    token_a = _register_and_login(client, email="a@example.com")
    token_b = _register_and_login(client, email="b@example.com")

    client.post(
        "/api/v1/clubs/me/players",
        json={
            "name": "player_a",
            "stats": {
                "strength": 60,
                "control": 60,
                "precision": 60,
                "agility": 60,
                "speed": 60,
            },
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )

    response = client.get(
        "/api/v1/clubs/me/players",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 200
    assert response.json() == []