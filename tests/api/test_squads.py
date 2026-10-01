"""Tests de API para el squad del club (PUT/GET /api/v1/clubs/me/squad)."""
from sqlalchemy import select

from app.models.behavior import Behavior, UserBehavior
from app.models.club import Club
from app.models.club_player import ClubPlayer
from app.models.user import User

PAYLOAD = {
    "username": "lara",
    "email": "lara_squad@example.com",
    "password": "12345678",
    "avatar": "1",
    "clubNombre": "club de lara",
}


def register_and_get_headers(client, payload=None):
    r = client.post("/api/v1/auth/register", json=payload or PAYLOAD)
    return {"Authorization": f"Bearer {r.json()['token']}"}


def get_user_by_email(db_session, email):
    return db_session.scalars(select(User).where(User.email == email)).first()


def _get_club_with_players_and_behavior(db_session, user_id):
    """El club ya lo crea register_user; acá solo le sumamos jugadores y un behavior."""
    club = db_session.scalars(select(Club).where(Club.user_id == user_id)).first()

    players = []
    for i in range(6):
        player = ClubPlayer(
            name=f"Player {i}",
            club_id=club.id,
            strength=50, control=50, precision=50, agility=50, speed=50,
        )
        db_session.add(player)
        players.append(player)
    db_session.commit()

    behavior = Behavior(name="Offensive", code="def decidir(contexto):\n    pass")
    db_session.add(behavior)
    db_session.commit()
    db_session.add(UserBehavior(user_id=user_id, behavior_id=behavior.id))
    db_session.commit()

    return club, players, behavior


def test_save_squad_success(client, db_session):
    """Guardar un squad válido devuelve 200 con la formación y los 6 miembros."""
    headers = register_and_get_headers(client)
    user = get_user_by_email(db_session, PAYLOAD["email"])
    _, players, behavior = _get_club_with_players_and_behavior(db_session, user.id)

    payload = {
        "formation": "1-2",
        "starters": [
            {"club_player_id": p.id, "behavior_id": behavior.id} for p in players[0:3]
        ],
        "substitutes": [
            {"club_player_id": p.id, "behavior_id": behavior.id} for p in players[3:6]
        ],
    }

    response = client.put("/api/v1/clubs/me/squad", json=payload, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["formation"] == "1-2"
    assert len(body["members"]) == 6


def test_get_squad_not_configured_returns_404(client, db_session):
    """Pedir el squad sin haberlo configurado antes devuelve 404."""
    headers = register_and_get_headers(client)

    response = client.get("/api/v1/clubs/me/squad", headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SQUAD_NOT_CONFIGURED"