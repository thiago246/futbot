"""Arranque del partido desde run_countdown: Match, MatchEngine y cierre del amistoso.

friendly_service y el motor abren sus propias sesiones (SessionLocal), así que el fixture
`session_factory` las apunta a la misma base en memoria que usa la fixture `db`.
Los datos de ClubPlayer/Behavior se stubbean con _load_player: acá se prueba el armado,
no esos modelos.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

import app.engine.match_engine as match_engine_module
from app.core.ws_manager import manager
from app.models.friendly import Friendly
from app.models.match import Match
from app.models.squads import FriendlySquadMember
from app.services import friendly_service


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def clean_rooms():
    manager.rooms.clear()
    yield
    manager.rooms.clear()


@pytest.fixture
def session_factory(db, monkeypatch):
    factory = sessionmaker(bind=db.get_bind(), autoflush=False)
    monkeypatch.setattr(friendly_service, "SessionLocal", factory)
    monkeypatch.setattr(match_engine_module, "SessionLocal", factory)
    return factory


class FakeWS:
    def __init__(self):
        self.sent: list[dict] = []
        self.closed_with: int | None = None

    async def accept(self):
        pass

    async def send_json(self, message: dict):
        self.sent.append(message)

    async def close(self, code: int = 1000):
        self.closed_with = code


def _fake_load_player(db, member):
    return SimpleNamespace(
        id=member.club_player_id, strength=60, control=60, precision=60, agility=60, speed=60,
        decide=lambda contexto: None,
    )


def _seed(db, status="cuenta_regresiva", duration=1) -> str:
    """Amistoso con las plantillas congeladas: 3 titulares + 3 suplentes por club."""
    friendly = Friendly(home_club_id="home", away_club_id="away", duration=duration, status=status)
    db.add(friendly)
    db.commit()
    fid = friendly.id
    for club, formation in (("home", "1-2"), ("away", "2-1")):
        for i in range(6):
            db.add(FriendlySquadMember(
                friendly_id=fid, club_id=club, formation=formation,
                club_player_id=f"{club}-p{i}", behavior_id=1, is_starter=i < 3,
            ))
    db.commit()
    return fid


# --------------------------------------------------------------- build_match_engine
def test_build_arma_participants_con_titulares_en_orden(db, monkeypatch):
    fid = _seed(db, duration=3)
    monkeypatch.setattr(friendly_service, "_load_player", _fake_load_player)

    engine = friendly_service.build_match_engine(db, fid)

    assert [p.id for p in engine.participants["home"]["players"]] == ["home-p0", "home-p1", "home-p2"]
    assert [p.id for p in engine.participants["away"]["players"]] == ["away-p0", "away-p1", "away-p2"]
    assert engine.participants["home"]["formation"] == "1-2"
    assert engine.participants["away"]["formation"] == "2-1"
    assert engine.duration_minutes == 3


def test_build_no_incluye_suplentes(db, monkeypatch):
    fid = _seed(db)
    monkeypatch.setattr(friendly_service, "_load_player", _fake_load_player)
    engine = friendly_service.build_match_engine(db, fid)
    ids = {p.id for side in engine.participants.values() for p in side["players"]}
    assert not ids & {"home-p3", "home-p4", "home-p5", "away-p3", "away-p4", "away-p5"}


def test_build_crea_el_match_con_el_mismo_id_que_el_amistoso(db, monkeypatch):
    fid = _seed(db)
    monkeypatch.setattr(friendly_service, "_load_player", _fake_load_player)

    engine = friendly_service.build_match_engine(db, fid)

    match = db.get(Match, fid)
    assert match is not None and match.friendly_id == fid and match.status == "in_progress"
    assert engine.match_id == fid
    assert engine.room == f"match:{fid}"


def test_build_dos_veces_no_duplica_el_match(db, monkeypatch):
    fid = _seed(db)
    monkeypatch.setattr(friendly_service, "_load_player", _fake_load_player)
    friendly_service.build_match_engine(db, fid)
    friendly_service.build_match_engine(db, fid)
    assert len(db.scalars(select(Match)).all()) == 1


# ------------------------------------------------------------------- run_countdown
@pytest.mark.anyio
async def test_run_countdown_pasa_a_en_curso_y_lanza_el_partido(db, session_factory):
    fid = _seed(db)
    with patch("asyncio.sleep", new_callable=AsyncMock), \
         patch.object(friendly_service, "_launch_match") as launch:
        await friendly_service.run_countdown(fid)

    with session_factory() as s:
        assert s.get(Friendly, fid).status == "en_curso"
    launch.assert_called_once_with(fid)


@pytest.mark.anyio
async def test_run_countdown_no_lanza_nada_si_ya_no_esta_en_cuenta_regresiva(db, session_factory):
    fid = _seed(db, status="finalizado")
    with patch("asyncio.sleep", new_callable=AsyncMock), \
         patch.object(friendly_service, "_launch_match") as launch:
        await friendly_service.run_countdown(fid)

    with session_factory() as s:
        assert s.get(Friendly, fid).status == "finalizado"
    launch.assert_not_called()


# ---------------------------------------------------------------------- run_match
@pytest.mark.anyio
async def test_run_match_juega_emite_y_deja_el_amistoso_finalizado(db, session_factory, monkeypatch):
    fid = _seed(db, status="en_curso")
    monkeypatch.setattr(friendly_service, "_load_player", _fake_load_player)
    ws = FakeWS()
    manager.rooms[f"match:{fid}"] = [ws]

    with patch.object(match_engine_module, "TICK_SECONDS", 0), \
         patch.object(match_engine_module, "ROOM_CLOSE_DELAY_SECONDS", 0.01):
        await friendly_service.run_match(fid)

    with session_factory() as s:
        friendly, match = s.get(Friendly, fid), s.get(Match, fid)
    assert friendly.status == "finalizado"
    assert match.status == "finished"
    assert ws.sent[0]["tipo"] == "tick"
    assert ws.sent[-1]["tipo"] == "partido_finalizado"


@pytest.mark.anyio
async def test_run_match_con_error_cierra_la_sala_y_finaliza_sin_propagar(db, session_factory, monkeypatch):
    fid = _seed(db, status="en_curso")

    def _roto(db, member):
        raise RuntimeError("jugador sin comportamiento")

    monkeypatch.setattr(friendly_service, "_load_player", _roto)
    ws = FakeWS()
    manager.rooms[f"match:{fid}"] = [ws]

    await friendly_service.run_match(fid)  # no debe lanzar

    with session_factory() as s:
        assert s.get(Friendly, fid).status == "finalizado"
    assert ws.closed_with == 1011
    assert f"match:{fid}" not in manager.rooms


# ----------------------------------------------------------------- _finalize_friendly
def test_finalize_copia_el_resultado_del_match(db, session_factory):
    fid = _seed(db, status="en_curso")
    db.add(Match(id=fid, friendly_id=fid, status="in_progress", home_score=2, away_score=1))
    db.commit()

    friendly_service._finalize_friendly(fid)

    with session_factory() as s:
        friendly, match = s.get(Friendly, fid), s.get(Match, fid)
    assert (friendly.status, friendly.home_score, friendly.away_score) == ("finalizado", 2, 1)
    assert match.status == "finished"


def test_finalize_sin_match_igual_finaliza(db, session_factory):
    fid = _seed(db, status="en_curso")
    friendly_service._finalize_friendly(fid)
    with session_factory() as s:
        assert s.get(Friendly, fid).status == "finalizado"
