"""Integración real de _persist_state con la DB (SQLite en memoria).

No usa mocks para la sesión: crea las tablas de verdad con el modelo Match tal
cual está en el repo, y verifica que el engine actualice la fila.
"""
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import club, user  # noqa: F401 (registran clubs/users en Base.metadata)
from app.models.friendly import Friendly
from app.models.match import Match

import app.engine.match_engine as match_engine_module
from app.engine.match_engine import MatchEngine


@pytest.fixture
def db_session(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    monkeypatch.setattr(match_engine_module, "SessionLocal", TestingSessionLocal)
    session = TestingSessionLocal()
    yield session
    session.close()


def _quieto(contexto):
    return None


def _players(*ids):
    return [
        SimpleNamespace(id=i, decide=_quieto, strength=60, control=60, precision=60, agility=60, speed=60)
        for i in ids
    ]


def _engine_with_match_row(db_session) -> tuple[MatchEngine, str]:
    friendly = Friendly(home_club_id="club-local-fake", duration=1)
    db_session.add(friendly)
    db_session.commit()

    match = Match(friendly_id=friendly.id, status="in_progress")
    db_session.add(match)
    db_session.commit()

    participants = {
        "home": {"players": _players(1, 2, 3), "formation": "1-2"},
        "away": {"players": _players(4, 5, 6), "formation": "2-1"},
    }
    engine = MatchEngine(str(match.id), participants, 1)
    engine.build_initial_state()
    return engine, match.id


def test_persist_state_actualiza_marcador_y_tick(db_session):
    engine, match_id = _engine_with_match_row(db_session)
    engine.state.home_score, engine.state.away_score = 2, 1
    engine.state.current_tick = 37

    engine._persist_state()

    fila = db_session.get(Match, match_id)
    assert (fila.home_score, fila.away_score, fila.minute) == (2, 1, 37)
    assert fila.status == "in_progress"


def test_persist_state_final_marca_finished(db_session):
    engine, match_id = _engine_with_match_row(db_session)

    engine._persist_state(final=True)

    fila = db_session.get(Match, match_id)
    assert fila.status == "finished"


def test_persist_state_no_guarda_posiciones(db_session):
    """REQ 14: las posiciones nunca deben persistirse."""
    engine, match_id = _engine_with_match_row(db_session)

    engine._persist_state()

    fila = db_session.get(Match, match_id)
    assert fila.state == {}  # nunca lo tocamos


def test_persist_state_sin_estado_no_hace_nada(db_session):
    engine, match_id = _engine_with_match_row(db_session)
    engine.discard_state()

    engine._persist_state()  # no debe explotar aunque state sea None

    fila = db_session.get(Match, match_id)
    assert fila.status == "in_progress"  # quedó como se creó, no se tocó