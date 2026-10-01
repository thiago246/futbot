"""Club squad service (REQ: Define club squad)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BehaviorNotAvailableError,
    DuplicatePlayersError,
    InsufficientPlayersError,
    InvalidFormationError,
    PlayerNotInClubError,
    SquadNotConfiguredError,
)
from app.models.squads import Squad, SquadMember
from app.models.user import User
from app.schemas.squads import SquadInput, SquadMemberInput, VALID_FORMATIONS
from app.services import behavior_service


def save_squad(db: Session, user: User, data: SquadInput) -> Squad:
    """Creates or replaces the club's squad (PUT /clubs/me/squad)."""

    if data.formation not in VALID_FORMATIONS:
        raise InvalidFormationError(f"Formation must be one of {VALID_FORMATIONS}")

    club = user.club

    if len(club.players) < 6:
        raise InsufficientPlayersError("The club needs at least 6 players")

    all_members: list[SquadMemberInput] = data.starters + data.substitutes
    sent_player_ids = [member.club_player_id for member in all_members]
    if len(sent_player_ids) != len(set(sent_player_ids)):
        raise DuplicatePlayersError("The 6 players must be different from each other")

    club_player_ids = {player.id for player in club.players}
    for player_id in sent_player_ids:
        if player_id not in club_player_ids:
            raise PlayerNotInClubError(f"Player {player_id} does not belong to this club")

    user_behaviors = behavior_service.list_behaviors(db, user)
    user_behavior_ids = {b.id for b in user_behaviors}
    for member in all_members:
        if member.behavior_id not in user_behavior_ids:
            raise BehaviorNotAvailableError(f"Behavior {member.behavior_id} is not available for this user")

    stmt = select(Squad).where(Squad.club_id == club.id)
    existing_squad = db.scalars(stmt).first()

    if existing_squad is not None:
        delete_stmt = select(SquadMember).where(SquadMember.squad_id == existing_squad.id)
        for old_member in db.scalars(delete_stmt).all():
            db.delete(old_member)
        squad = existing_squad
        squad.formation = data.formation
    else:
        squad = Squad(club_id=club.id, formation=data.formation)
        db.add(squad)
        db.flush()

    for member in data.starters:
        db.add(SquadMember(
            squad_id=squad.id,
            club_player_id=member.club_player_id,
            behavior_id=member.behavior_id,
            is_starter=True,
        ))
    for member in data.substitutes:
        db.add(SquadMember(
            squad_id=squad.id,
            club_player_id=member.club_player_id,
            behavior_id=member.behavior_id,
            is_starter=False,
        ))

    db.commit()
    db.refresh(squad)
    return squad


def get_squad(db: Session, user: User) -> Squad:
    """Returns the club's squad (GET /clubs/me/squad). 404 if not configured yet."""
    club = user.club

    stmt = select(Squad).where(Squad.club_id == club.id)
    squad = db.scalars(stmt).first()

    if squad is None:
        raise SquadNotConfiguredError("This club has no squad configured yet")

    return squad