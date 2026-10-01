"""Lógica de amistosos."""
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import (
    CannotJoinOwnMatchError,
    FriendlyNotFoundError,
    InvalidDurationError,
    MatchFullError,
    MatchNotAvailableError,
    SquadRequiredError,
)
from app.models.friendly import Friendly
from app.models.squads import Squad
from app.models.user import User
from app.schemas.friendly import FriendlyCreate

VALID_DURATIONS = (1, 3, 5)


def _require_default_squad(db: Session, club_id: str, message: str) -> None:
    """Lanza SquadRequiredError (422) si el club no tiene plantilla default.

    Consultamos la tabla directo y no con squads_service.get_squad(), porque esa
    función lanza SquadNotConfiguredError (404), que es lo correcto para
    GET /clubs/me/squad pero no para crear/unirse/iniciar un amistoso.
    """
    squad = db.scalars(select(Squad).where(Squad.club_id == club_id)).first()
    if squad is None:
        raise SquadRequiredError(message)


def create_friendly(db: Session, user: User, data: FriendlyCreate) -> Friendly:
    """Crear amistoso (POST /matches).

    - 422 INVALID_DURATION si la duración no es 1, 3 o 5.
    - 422 SQUAD_NOT_CONFIGURED si el club no tiene plantilla default.
    - El club del usuario queda como home_club_id, sin rival, en "esperando_rival".
    """
    if data.duration not in VALID_DURATIONS:
        raise InvalidDurationError("La duración debe ser 1, 3 o 5 minutos")

    club = user.club
    _require_default_squad(
        db, club.id, "Configure su plantilla antes de crear un amistoso"
    )

    friendly = Friendly(home_club_id=club.id, duration=data.duration)
    db.add(friendly)
    db.commit()
    db.refresh(friendly)
    return friendly


def list_friendlies(
    db: Session,
    status: str | None = None,
    kind: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Friendly], int]:
    """Listar amistosos (GET /matches). Devuelve (items de la página, total).

    - Los filtros status y kind son opcionales y se combinan.
    - Orden: los más antiguos primero (los que más tiempo llevan esperando).
    - kind="liga" devuelve vacío: esta tabla solo tiene amistosos. No es un error.
    """
    query = select(Friendly)
    count_query = select(func.count()).select_from(Friendly)
    if status is not None:
        query = query.where(Friendly.status == status)
        count_query = count_query.where(Friendly.status == status)
    if kind is not None:
        query = query.where(Friendly.kind == kind)
        count_query = count_query.where(Friendly.kind == kind)

    total = db.scalar(count_query)
    items = db.scalars(
        query.order_by(Friendly.created_at.asc(), Friendly.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def join_friendly(db: Session, user: User, friendly_id: str) -> Friendly:
    """Unirse a un amistoso como visitante (POST /matches/{id}/join).

    Orden de validación:
    - 404 MATCH_NOT_FOUND si el amistoso no existe.
    - 409 CANNOT_JOIN_OWN_MATCH si el club propio es el local.
    - 409 MATCH_FULL si ya tiene club visitante.
    - 409 MATCH_NOT_AVAILABLE si no está en "esperando_rival".
    - 422 SQUAD_NOT_CONFIGURED si el club no tiene plantilla default.
    Si todo va bien, el club queda como away_club_id y el partido pasa a "programado".
    """
    friendly = db.get(Friendly, friendly_id)
    if friendly is None:
        raise FriendlyNotFoundError("Partido no encontrado")

    club = user.club
    if friendly.home_club_id == club.id:
        raise CannotJoinOwnMatchError("No podés unirte a tu propio partido")
    if friendly.away_club_id is not None:
        raise MatchFullError("El partido ya tiene los dos clubes asignados")
    if friendly.status != "esperando_rival":
        raise MatchNotAvailableError("El partido no está disponible para unirse")

    _require_default_squad(
        db, club.id, "Configure su plantilla antes de unirse a un amistoso"
    )

    # UPDATE condicional: si dos clubes se unen a la vez, solo uno cumple la condición
    # (rowcount == 1) y el otro recibe MATCH_FULL, sin pisar al primero.
    result = db.execute(
        update(Friendly)
        .where(
            Friendly.id == friendly.id,
            Friendly.away_club_id.is_(None),
            Friendly.status == "esperando_rival",
        )
        .values(away_club_id=club.id, status="programado")
    )
    if result.rowcount != 1:
        db.rollback()
        raise MatchFullError("El partido ya tiene los dos clubes asignados")

    db.commit()
    db.refresh(friendly)
    return friendly


def start_friendly(db: Session, user: User, friendly_id: str) -> Friendly:
    """Iniciar el partido. (pendiente)"""
    raise NotImplementedError("Iniciar partido")