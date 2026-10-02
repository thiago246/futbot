"""Tests unitarios de services/friendly_service.py

Por ahora solo Crear amistoso.
"""
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import (
    BehaviorInUseError,
    CannotJoinOwnMatchError,
    FriendlyNotFoundError,
    InvalidDurationError,
    MatchFullError,
    MatchNotAvailableError,
    SquadRequiredError,
)
from app.models.behavior import Behavior
from app.models.club import Club
from app.models.club_player import ClubPlayer
from app.models.friendly import Friendly
from app.models.squads import FriendlySquadMember, Squad, SquadMember
from app.models.user import User
from app.schemas.friendly import FriendlyCreate
from app.services import friendly_service


def _create_club(db, user, name="Los Larry"):
    club = Club(nombre=name, user_id=user.id)  # Club.nombre: columna de otro módulo
    db.add(club)
    db.commit()
    db.refresh(club)
    return club


def _create_default_squad(db, club):
    """Inserta directo en la DB una plantilla válida (6 jugadores, 3 titulares + 3 suplentes),
    para no depender de squads_service en estos tests."""
    # 6 comportamientos distintos (un club no puede repetir uno en su plantilla).
    # Se reutilizan entre clubes: distintos clubes sí pueden usar el mismo.
    behaviors = []
    for i in range(6):
        behavior = db.query(Behavior).filter_by(name=f"test-behavior-{i}").first()
        if behavior is None:
            behavior = Behavior(name=f"test-behavior-{i}", code="pass", is_default=False)
            db.add(behavior)
            db.flush()
        behaviors.append(behavior)

    players = [
        ClubPlayer(
            name=f"Player {i}", strength=60, control=60, precision=60,
            agility=60, speed=60, club_id=club.id,
        )
        for i in range(6)
    ]
    db.add_all(players)
    db.flush()

    squad = Squad(club_id=club.id, formation="1-2")
    db.add(squad)
    db.flush()

    for i, player in enumerate(players):
        db.add(SquadMember(
            squad_id=squad.id,
            club_player_id=player.id,
            behavior_id=behaviors[i].id,
            is_starter=i < 3,
        ))
    db.commit()
    return squad


@pytest.fixture()
def club(db, user):
    return _create_club(db, user)


@pytest.fixture()
def club_with_squad(db, club):
    _create_default_squad(db, club)
    return club


def test_create_friendly_starts_waiting_for_opponent_with_club_as_home(db, user, club_with_squad):
    friendly = friendly_service.create_friendly(db, user, FriendlyCreate(duration=3))

    uuid.UUID(friendly.id)  # el id es un UUID válido
    assert friendly.kind == "amistoso"
    assert friendly.status == "esperando_rival"
    assert friendly.home_club_id == club_with_squad.id
    assert friendly.away_club_id is None
    assert friendly.duration == 3
    assert friendly.home_score == 0
    assert friendly.away_score == 0
    assert friendly.remaining_substitutions == 3


def test_create_friendly_is_persisted_in_db(db, user, club_with_squad):
    created = friendly_service.create_friendly(db, user, FriendlyCreate(duration=1))

    saved = db.get(Friendly, created.id)
    assert saved is not None
    assert saved.home_club_id == club_with_squad.id


@pytest.mark.parametrize("duration", [1, 3, 5])
def test_create_friendly_accepts_valid_durations(db, user, club_with_squad, duration):
    friendly = friendly_service.create_friendly(db, user, FriendlyCreate(duration=duration))

    assert friendly.duration == duration


@pytest.mark.parametrize("duration", [-1, 0, 2, 4, 6, 10])
def test_create_friendly_rejects_invalid_duration(db, user, club_with_squad, duration):
    with pytest.raises(InvalidDurationError):
        friendly_service.create_friendly(db, user, FriendlyCreate(duration=duration))

    assert db.query(Friendly).count() == 0


def test_create_friendly_rejects_club_without_squad(db, user, club):
    with pytest.raises(SquadRequiredError):
        friendly_service.create_friendly(db, user, FriendlyCreate(duration=3))

    assert db.query(Friendly).count() == 0


def test_create_friendly_validates_duration_before_squad(db, user, club):
    """Sin plantilla y con duración inválida, el error que se informa es el de la duración."""
    with pytest.raises(InvalidDurationError):
        friendly_service.create_friendly(db, user, FriendlyCreate(duration=2))


# ---------------------------------------------------------------------------
# Listar amistosos
# ---------------------------------------------------------------------------
T0 = datetime(2026, 1, 1, 12, 0, 0)


def _insert_friendly(db, status="esperando_rival", kind="amistoso", minutes=0,
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
    db.add(friendly)
    db.commit()
    db.refresh(friendly)
    return friendly


def test_list_friendlies_returns_only_requested_status(db):
    waiting_1 = _insert_friendly(db, "esperando_rival", minutes=0)
    _insert_friendly(db, "en_curso", minutes=1)
    waiting_2 = _insert_friendly(db, "esperando_rival", minutes=2)
    _insert_friendly(db, "finalizado", minutes=3)

    items, total = friendly_service.list_friendlies(db, status="esperando_rival")

    assert [f.id for f in items] == [waiting_1.id, waiting_2.id]
    assert total == 2


def test_list_friendlies_can_filter_by_scheduled_status(db):
    _insert_friendly(db, "esperando_rival", minutes=0)
    scheduled = _insert_friendly(db, "programado", minutes=1)

    items, total = friendly_service.list_friendlies(db, status="programado")

    assert [f.id for f in items] == [scheduled.id]
    assert total == 1


def test_list_friendlies_returns_only_requested_kind(db):
    friendly = _insert_friendly(db, kind="amistoso", minutes=0)
    _insert_friendly(db, kind="liga", minutes=1)

    items, total = friendly_service.list_friendlies(db, kind="amistoso")

    assert [f.id for f in items] == [friendly.id]
    assert total == 1


def test_list_friendlies_kind_liga_returns_empty_without_error(db):
    _insert_friendly(db, kind="amistoso")

    items, total = friendly_service.list_friendlies(db, kind="liga")

    assert items == []
    assert total == 0


def test_list_friendlies_combines_status_and_kind(db):
    match = _insert_friendly(db, status="esperando_rival", kind="amistoso", minutes=0)
    _insert_friendly(db, status="en_curso", kind="amistoso", minutes=1)
    _insert_friendly(db, status="esperando_rival", kind="liga", minutes=2)

    items, total = friendly_service.list_friendlies(db, status="esperando_rival", kind="amistoso")

    assert [f.id for f in items] == [match.id]
    assert total == 1


def test_list_friendlies_without_filters_returns_all(db):
    _insert_friendly(db, "esperando_rival", minutes=0)
    _insert_friendly(db, "en_curso", minutes=1)
    _insert_friendly(db, "finalizado", minutes=2)

    items, total = friendly_service.list_friendlies(db)

    assert len(items) == 3
    assert total == 3


def test_list_friendlies_empty(db):
    assert friendly_service.list_friendlies(db) == ([], 0)


def test_list_friendlies_orders_oldest_first(db):
    newest = _insert_friendly(db, minutes=10)
    oldest = _insert_friendly(db, minutes=0)
    middle = _insert_friendly(db, minutes=5)

    items, _ = friendly_service.list_friendlies(db)

    assert [f.id for f in items] == [oldest.id, middle.id, newest.id]


def test_list_friendlies_paginates(db):
    created = [_insert_friendly(db, minutes=i) for i in range(5)]

    page_1, total_1 = friendly_service.list_friendlies(db, page=1, page_size=2)
    page_3, total_3 = friendly_service.list_friendlies(db, page=3, page_size=2)
    page_4, total_4 = friendly_service.list_friendlies(db, page=4, page_size=2)

    assert [f.id for f in page_1] == [created[0].id, created[1].id]
    assert [f.id for f in page_3] == [created[4].id]
    assert page_4 == []
    assert total_1 == total_3 == total_4 == 5  # total es el de los filtros, no el de la página


def test_list_friendlies_total_ignores_pagination_but_respects_filters(db):
    for i in range(3):
        _insert_friendly(db, "esperando_rival", minutes=i)
    _insert_friendly(db, "en_curso", minutes=10)

    items, total = friendly_service.list_friendlies(db, status="esperando_rival", page_size=2)

    assert len(items) == 2
    assert total == 3


# ---------------------------------------------------------------------------
# Unirse a amistoso
# ---------------------------------------------------------------------------
def _create_user(db, email):
    user = User(username=email.split("@")[0], email=email, password_hash="pass")
    db.add(user)
    db.commit()
    return user


@pytest.fixture()
def rival(db):
    """Segundo usuario, con club pero sin plantilla."""
    user = _create_user(db, "rival@gmail.com")
    _create_club(db, user, name="Los Rivales")
    return user


@pytest.fixture()
def rival_with_squad(db, rival):
    _create_default_squad(db, rival.club)
    return rival


@pytest.fixture()
def home_friendly(db, user, club_with_squad):
    """Amistoso creado por `user`, esperando rival."""
    return friendly_service.create_friendly(db, user, FriendlyCreate(duration=3))


def _assert_unchanged(db, friendly):
    db.refresh(friendly)
    assert friendly.away_club_id is None
    assert friendly.status == "esperando_rival"


def test_join_friendly_assigns_club_as_away_and_starts_countdown(db, club_with_squad, rival_with_squad, home_friendly):
    joined = friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    assert joined.id == home_friendly.id
    assert joined.away_club_id == rival_with_squad.club.id
    assert joined.home_club_id == club_with_squad.id
    assert joined.status == "cuenta_regresiva"


def test_join_friendly_is_persisted_in_db(db, rival_with_squad, home_friendly):
    friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    db.expire_all()
    saved = db.get(Friendly, home_friendly.id)
    assert saved.away_club_id == rival_with_squad.club.id
    assert saved.status == "cuenta_regresiva"


def test_join_friendly_rejects_own_match(db, user, home_friendly):
    with pytest.raises(CannotJoinOwnMatchError):
        friendly_service.join_friendly(db, user, home_friendly.id)

    _assert_unchanged(db, home_friendly)


def test_join_friendly_rejects_match_that_already_has_away_club(db, club_with_squad, rival_with_squad):
    full = _insert_friendly(
        db, status="programado", home_club_id=club_with_squad.id, away_club_id="otro-club"
    )

    with pytest.raises(MatchFullError):
        friendly_service.join_friendly(db, rival_with_squad, full.id)

    db.refresh(full)
    assert full.away_club_id == "otro-club"


def test_join_friendly_twice_with_same_club_is_rejected_as_full(db, rival_with_squad, home_friendly):
    friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    with pytest.raises(MatchFullError):
        friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)


@pytest.mark.parametrize("status", ["cuenta_regresiva", "en_curso", "pausado", "finalizado"])
def test_join_friendly_rejects_match_not_waiting_for_rival(db, club_with_squad, rival_with_squad, status):
    friendly = _insert_friendly(db, status=status, home_club_id=club_with_squad.id)

    with pytest.raises(MatchNotAvailableError):
        friendly_service.join_friendly(db, rival_with_squad, friendly.id)

    db.refresh(friendly)
    assert friendly.away_club_id is None
    assert friendly.status == status


def test_join_friendly_rejects_club_without_squad(db, rival, home_friendly):
    with pytest.raises(SquadRequiredError):
        friendly_service.join_friendly(db, rival, home_friendly.id)

    _assert_unchanged(db, home_friendly)


def test_join_friendly_rejects_unknown_match(db, rival_with_squad):
    with pytest.raises(FriendlyNotFoundError):
        friendly_service.join_friendly(db, rival_with_squad, str(uuid.uuid4()))


def test_join_friendly_checks_own_match_before_squad(db, user, club):
    """El club propio no tiene plantilla, pero el error que se informa es el de partido propio."""
    own = _insert_friendly(db, home_club_id=club.id)

    with pytest.raises(CannotJoinOwnMatchError):
        friendly_service.join_friendly(db, user, own.id)


def test_join_friendly_checks_full_match_before_squad(db, rival):
    full = _insert_friendly(db, status="programado", away_club_id="otro-club")

    with pytest.raises(MatchFullError):
        friendly_service.join_friendly(db, rival, full.id)


def test_join_friendly_loses_race_when_another_club_joins_first(
    db, rival_with_squad, home_friendly, monkeypatch
):
    """Otro club se une entre la validación y el guardado: este recibe MATCH_FULL
    y el primero no queda pisado."""
    other = _create_club(db, _create_user(db, "other@gmail.com"), name="Otro club")
    original = friendly_service._require_default_squad

    def check_squad_then_other_club_sneaks_in(db_, club_id, message):
        original(db_, club_id, message)
        db_.execute(
            update(Friendly)
            .where(Friendly.id == home_friendly.id)
            .values(away_club_id=other.id, status="programado")
        )
        db_.commit()

    monkeypatch.setattr(friendly_service, "_require_default_squad", check_squad_then_other_club_sneaks_in)

    with pytest.raises(MatchFullError):
        friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    db.refresh(home_friendly)
    assert home_friendly.away_club_id == other.id

# ---------------------------------------------------------------------------
# Inicio automático al unirse: plantillas congeladas y cuenta regresiva
# ---------------------------------------------------------------------------
@pytest.fixture()
def anyio_backend():
    return "asyncio"


def _snapshot(db, friendly_id, club_id=None):
    query = db.query(FriendlySquadMember).filter_by(friendly_id=friendly_id)
    if club_id is not None:
        query = query.filter_by(club_id=club_id)
    return query.order_by(FriendlySquadMember.id).all()


def _squad_members(db, club_id):
    return (
        db.query(SquadMember)
        .join(Squad, SquadMember.squad_id == Squad.id)
        .filter(Squad.club_id == club_id)
        .order_by(SquadMember.id)
        .all()
    )


def test_join_friendly_freezes_both_squads(db, club_with_squad, rival_with_squad, home_friendly):
    """Ambos clubes usan los mismos 6 comportamientos (los crea el helper una sola vez):
    clubes distintos sí pueden compartir comportamientos."""
    friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    for club in (club_with_squad, rival_with_squad.club):
        rows = _snapshot(db, home_friendly.id, club.id)
        assert len(rows) == 6
        assert sum(r.is_starter for r in rows) == 3
        assert {r.formation for r in rows} == {"1-2"}
        assert len({r.behavior_id for r in rows}) == 6
    assert len(_snapshot(db, home_friendly.id)) == 12


def test_join_friendly_snapshot_ignores_later_squad_edits(db, club_with_squad, rival_with_squad, home_friendly):
    friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    squad = db.query(Squad).filter_by(club_id=club_with_squad.id).one()
    squad.formation = "2-1"
    db.commit()

    assert {r.formation for r in _snapshot(db, home_friendly.id, club_with_squad.id)} == {"1-2"}


def test_join_friendly_rejected_does_not_freeze_anything(db, user, home_friendly):
    with pytest.raises(CannotJoinOwnMatchError):
        friendly_service.join_friendly(db, user, home_friendly.id)

    assert _snapshot(db, home_friendly.id) == []


def test_join_friendly_twice_does_not_freeze_again(db, rival_with_squad, home_friendly):
    friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    with pytest.raises(MatchFullError):
        friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    assert len(_snapshot(db, home_friendly.id)) == 12


def test_join_friendly_rejects_incomplete_home_squad(db, club_with_squad, rival_with_squad, home_friendly):
    """El local pudo editar su plantilla después de publicar el amistoso."""
    squad = db.query(Squad).filter_by(club_id=club_with_squad.id).one()
    db.delete(squad.members[-1])
    db.commit()

    with pytest.raises(SquadRequiredError):
        friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    _assert_unchanged(db, home_friendly)
    assert _snapshot(db, home_friendly.id) == []


def test_join_friendly_rejects_incomplete_away_squad(db, rival_with_squad, home_friendly):
    squad = db.query(Squad).filter_by(club_id=rival_with_squad.club.id).one()
    db.delete(squad.members[-1])
    db.commit()

    with pytest.raises(SquadRequiredError):
        friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    _assert_unchanged(db, home_friendly)
    assert _snapshot(db, home_friendly.id) == []


@pytest.mark.parametrize("repeats", ["home", "away"])
def test_join_friendly_rejects_club_that_repeats_a_behavior(
    db, club_with_squad, rival_with_squad, home_friendly, repeats
):
    """Un comportamiento puede usarse en varios partidos, pero un mismo club no
    puede usarlo dos veces dentro del mismo partido."""
    club_id = club_with_squad.id if repeats == "home" else rival_with_squad.club.id
    members = _squad_members(db, club_id)
    members[1].behavior_id = members[0].behavior_id
    db.commit()

    with pytest.raises(BehaviorInUseError):
        friendly_service.join_friendly(db, rival_with_squad, home_friendly.id)

    _assert_unchanged(db, home_friendly)
    assert _snapshot(db, home_friendly.id) == []


# --- cuenta regresiva ------------------------------------------------------
def test_countdown_lasts_15_seconds():
    assert friendly_service.COUNTDOWN_SECONDS == 15


@pytest.fixture()
def fast_countdown(db, monkeypatch):
    """Sin esperar 15 s y con run_countdown usando la misma DB de los tests."""
    monkeypatch.setattr(friendly_service, "COUNTDOWN_SECONDS", 0)
    monkeypatch.setattr(friendly_service, "SessionLocal", sessionmaker(bind=db.get_bind()))


@pytest.mark.anyio
async def test_run_countdown_moves_match_to_in_progress(db, fast_countdown):
    friendly = _insert_friendly(db, status="cuenta_regresiva", away_club_id="otro-club")

    await friendly_service.run_countdown(friendly.id)

    db.expire_all()
    assert db.get(Friendly, friendly.id).status == "en_curso"


@pytest.mark.anyio
@pytest.mark.parametrize("status", ["esperando_rival", "en_curso", "finalizado"])
async def test_run_countdown_does_not_touch_match_that_is_not_in_countdown(db, fast_countdown, status):
    friendly = _insert_friendly(db, status=status)

    await friendly_service.run_countdown(friendly.id)

    db.expire_all()
    assert db.get(Friendly, friendly.id).status == status