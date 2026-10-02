"""Lógica de amistosos."""
import asyncio

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.exceptions import (
    BehaviorInUseError,
    CannotJoinOwnMatchError,
    FriendlyNotFoundError,
    InvalidDurationError,
    MatchFullError,
    MatchNotAvailableError,
    SquadRequiredError,
)
from app.models.friendly import Friendly
from app.models.squads import FriendlySquadMember, Squad, SquadMember
from app.models.user import User
from app.schemas.friendly import FriendlyCreate

VALID_DURATIONS = (1, 3, 5)
COUNTDOWN_SECONDS = 15


def _require_default_squad(db: Session, club_id: str, message: str) -> None:
    """Lanza SquadRequiredError (422) si el club no tiene plantilla default.

    Consultamos la tabla directo y no con squads_service.get_squad(), porque esa
    función lanza SquadNotConfiguredError (404), que es lo correcto para
    GET /clubs/me/squad pero no para crear/unirse a un amistoso.
    """
    squad = db.scalars(select(Squad).where(Squad.club_id == club_id)).first()
    if squad is None:
        raise SquadRequiredError(message)


def _load_squad(db: Session, club_id: str) -> tuple[str, list[SquadMember]]:
    """Plantilla vigente del club, validada para jugar. Devuelve (formación, miembros).

    - 422 SQUAD_NOT_CONFIGURED si el club no tiene plantilla o está incompleta
    - 409 BEHAVIOR_IN_USE si el club repite un comportamiento en la plantilla:
      un comportamiento puede usarse en varios partidos (y por varios clubes),
      pero un mismo club no puede usarlo dos veces dentro del mismo partido.

    El club tiene una sola plantilla: si la editó para crear/unirse, esa es la vigente.
    """
    squad = db.scalars(select(Squad).where(Squad.club_id == club_id)).first()
    if squad is None:
        raise SquadRequiredError(
            "Alguno de los clubes no tiene una plantilla disponible para jugar"
        )

    members = sorted(squad.members, key=lambda m: m.id)
    starters = sum(1 for m in members if m.is_starter)
    if starters != 3 or len(members) - starters != 3:
        raise SquadRequiredError(
            "Alguno de los clubes tiene una plantilla incompleta (se necesitan 3 titulares y 3 suplentes)"
        )

    behavior_ids = [m.behavior_id for m in members]
    if len(set(behavior_ids)) != len(behavior_ids):
        raise BehaviorInUseError()

    return squad.formation, members


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

    Unirse INICIA el partido: no hay un paso de "iniciar" aparte. Con el rival
    asignado, el partido congela las plantillas de ambos clubes y arranca la
    cuenta regresiva (el router agenda run_countdown).

    Orden de validación:
    - 404 MATCH_NOT_FOUND si el amistoso no existe.
    - 409 CANNOT_JOIN_OWN_MATCH si el club propio es el local.
    - 409 MATCH_FULL si ya tiene club visitante.
    - 409 MATCH_NOT_AVAILABLE si no está en "esperando_rival".
    - 422 SQUAD_NOT_CONFIGURED si el club propio no tiene plantilla default.
    - 422 SQUAD_NOT_CONFIGURED si la plantilla de alguno de los dos clubes
      está incompleta (no son 3 titulares + 3 suplentes).
    - 409 BEHAVIOR_IN_USE si alguno de los dos clubes repite un comportamiento.
    Si todo va bien, en una sola transacción: el club queda como away_club_id,
    se congelan las plantillas de ambos clubes y el partido pasa a "cuenta_regresiva".
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

    # Plantillas de los dos clubes, validadas, listas para congelar. El local pudo
    # haber editado la suya desde que publicó el amistoso, por eso se vuelve a validar.
    squads = {
        club_id: _load_squad(db, club_id)
        for club_id in (friendly.home_club_id, club.id)
    }

    # UPDATE condicional: si dos clubes se unen a la vez, solo uno cumple la condición
    # (rowcount == 1) y el otro recibe MATCH_FULL, sin pisar al primero ni congelar nada.
    result = db.execute(
        update(Friendly)
        .where(
            Friendly.id == friendly.id,
            Friendly.away_club_id.is_(None),
            Friendly.status == "esperando_rival",
        )
        .values(away_club_id=club.id, status="cuenta_regresiva")
    )
    if result.rowcount != 1:
        db.rollback()
        raise MatchFullError("El partido ya tiene los dos clubes asignados")

    for club_id, (formation, members) in squads.items():
        for member in members:
            db.add(
                FriendlySquadMember(
                    friendly_id=friendly.id,
                    club_id=club_id,
                    formation=formation,
                    club_player_id=member.club_player_id,
                    behavior_id=member.behavior_id,
                    is_starter=member.is_starter,
                )
            )

    db.commit()
    db.refresh(friendly)
    return friendly


async def run_countdown(friendly_id: str) -> None:
    """Cuenta regresiva: espera COUNTDOWN_SECONDS y pasa el partido a "en_curso".

    Se agenda desde el router con BackgroundTasks. Abre su propia sesión porque la
    del request ya se cerró. El UPDATE es condicional: si el partido ya no está en
    "cuenta_regresiva", no lo toca.

    Limitación conocida: si el servidor se reinicia durante la cuenta, el partido
    queda en "cuenta_regresiva".
    """
    await asyncio.sleep(COUNTDOWN_SECONDS)
    with SessionLocal() as db:
        db.execute(
            update(Friendly)
            .where(Friendly.id == friendly_id, Friendly.status == "cuenta_regresiva")
            .values(status="en_curso")
        )
        db.commit()
    # Acá se engancha el arranque del motor (MatchEngine) cuando se integre.