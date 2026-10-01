from unittest.mock import patch
from app.models.user import User


def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "thiago",
            "email": "thiago@example.com",
            "password": "12345678",
            "avatar": "hola",
            "clubNombre": "los thiagos",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "thiago@example.com"
    assert body["club"]["nombre"] == "los thiagos"
    assert "token" in body


def test_register_duplicate_email(client):
    payload = {
        "username": "thiago",
        "email": "thiago@example.com",
        "password": "12345678",
        "avatar": "hola",
        "clubNombre": "los thiagos",
    }

    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"

def test_register_missing_fields(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "thiago",
            # Omitimos intencionalmente el resto de los campos requeridos
        },
    )

    assert response.status_code == 422

def test_register_empty_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "thiago",
            "email": "empty-pass@example.com",
            "password": "",
            "avatar": "hola",
            "clubNombre": "club vacio",
        },
    )
    assert response.status_code == 422

def test_register_invalid_email_format(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "thiago",
            "email": "esto-no-es-un-email",  # Formato inválido
            "password": "1234",
            "avatar": "https://ejemplo.com/avatar.png",
            "clubNombre": "los thiagos",
        },
    )

    assert response.status_code == 422


def test_register_atomicity_rollback(client, db_session):
    payload = {
        "username": "thiago_atomico",
        "email": "thiago_atomico@example.com",
        "password": "12345678",
        "avatar": "hola",
        "clubNombre": "los thiagos atomicos",
    }

    with patch("sqlalchemy.orm.Session.commit", side_effect=Exception("Error simulado al guardar")):
        response = client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 500

    usuario_en_db = db_session.query(User).filter_by(email="thiago_atomico@example.com").first()
    
    assert usuario_en_db is None

def _registrar_usuario(client, email="thiago@example.com", password="1234"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "username": "thiago",
            "email": email,
            "password": password,
            "avatar": "hola",
            "clubNombre": "los thiagos",
        },
    )


def test_login_success(client):
    _registrar_usuario(client, email="login@example.com", password="12345678")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "12345678"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "token" in body
    assert "userId" in body


def test_login_wrong_password(client):
    _registrar_usuario(client, email="login2@example.com", password="1234")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login2@example.com", "password": "incorrecta"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_nonexistent_email(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "no-existe@example.com", "password": "cualquiera"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"