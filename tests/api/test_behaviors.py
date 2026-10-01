from sqlalchemy import select

from app.models.behavior import Behavior, UserBehavior
from app.models.user import User

PAYLOAD = {
    "username": "lara",
    "email": "lara@example.com",
    "password": "12345678",
    "avatar": "1",
    "clubNombre": "club de lara",
}

PAYLOAD_2 = {
    "username": "other",
    "email": "other@example.com",
    "password": "12345678",
    "avatar": "1",
    "clubNombre": "other club",
}


def register_and_headers(client):
    r = client.post("/api/v1/auth/register", json=PAYLOAD)
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_list_behaviors_sin_token(client):
    response = client.get("/api/v1/behaviors", headers={"Authorization": "Bearer basura"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_list_behaviors_usuario_nuevo(client):
    headers = register_and_headers(client)
    response = client.get("/api/v1/behaviors", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_behaviors_incluye_isdefault(client, db_session):
    headers = register_and_headers(client)
    user = db_session.scalars(
        select(User).where(User.email == PAYLOAD["email"])
    ).first()
    default = Behavior(name="CustomDefault", code="def decidir(contexto):\n    pass")
    custom = Behavior(
        name="Mine", code="def decidir(contexto):\n    pass", is_default=False
    )
    db_session.add_all([default, custom])
    db_session.commit()
    db_session.add_all([
        UserBehavior(user_id=user.id, behavior_id=default.id),
        UserBehavior(user_id=user.id, behavior_id=custom.id),
    ])
    db_session.commit()

    response = client.get("/api/v1/behaviors", headers=headers)

    assert response.status_code == 200
    body = response.json()
    by_name = {b["name"]: b for b in body}
    assert by_name["CustomDefault"]["isDefault"] is True
    assert by_name["Mine"]["isDefault"] is False

def register_other_and_headers(client):
    r = client.post("/api/v1/auth/register", json=PAYLOAD_2)
    return {"Authorization": f"Bearer {r.json()['token']}"}


def create_behavior_for(db_session, email, name="CustomBehavior", is_default=True):
    user = db_session.scalars(select(User).where(User.email == email)).first()
    behavior = Behavior(
        name=name,
        code="def decidir(contexto):\n    pass",
        is_default=is_default,
    )
    db_session.add(behavior)
    db_session.commit()
    db_session.add(UserBehavior(user_id=user.id, behavior_id=behavior.id))
    db_session.commit()
    return behavior


def test_get_behavior_without_token(client):
    response = client.get(
        "/api/v1/behaviors/1", headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 401


def test_get_behavior_detail(client, db_session):
    headers = register_and_headers(client)
    behavior = create_behavior_for(db_session, PAYLOAD["email"])

    response = client.get(f"/api/v1/behaviors/{behavior.id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "CustomBehavior"
    assert body["code"] == "def decidir(contexto):\n    pass"
    assert body["isDefault"] is True


def test_get_behavior_not_found(client):
    headers = register_and_headers(client)

    response = client.get("/api/v1/behaviors/9999", headers=headers)

    assert response.status_code == 404


def test_get_behavior_of_other_user(client, db_session):
    headers = register_and_headers(client)
    register_other_and_headers(client)
    other_behavior = create_behavior_for(
        db_session, PAYLOAD_2["email"], name="NotMine", is_default=False
    )

    response = client.get(f"/api/v1/behaviors/{other_behavior.id}", headers=headers)

    assert response.status_code == 404


def test_new_user_has_3_default_behaviors(client):
    headers = register_and_headers(client)

    response = client.get("/api/v1/behaviors", headers=headers)

    body = response.json()
    assert len(body) == 3
    assert all(b["isDefault"] for b in body)
    assert {b["name"] for b in body} == {"Ofensivo", "Defensivo", "Equilibrado"}