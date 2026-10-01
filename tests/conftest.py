"""Fixtures comunes.

- `db` es una sesión sobre SQLite en memoria, para los tests unitarios de services.
- El `client` vive en tests/api/conftest.py (lo define Thiago).
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.user import User

from app import models 
from app.core.database import Base

class FakePlayer:
    id = "1"

    def __init__(self):
        self.calls = []

    def mover_hacia(self, d): self.calls.append(("move", d))
    def patear_hacia(self, d): self.calls.append(("kick", d))
    def intentar_robar(self, r): self.calls.append(("steal", r))


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def player():
    return FakePlayer()


@pytest.fixture()
def user(db):
    user = User(username="larry", email="larry@gmail.com", password_hash="pass")
    db.add(user)
    db.commit()
    return user