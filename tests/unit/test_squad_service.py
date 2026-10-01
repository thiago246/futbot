from app.models.club import Club
from app.models.club_player import ClubPlayer
from app.services import squads_service
from app.schemas.squads import SquadInput, SquadMemberInput
import pytest
from app.models.behavior import Behavior, UserBehavior
from app.core.exceptions import (
    InvalidFormationError,
    InsufficientPlayersError,
    DuplicatePlayersError,
    PlayerNotInClubError,
    BehaviorNotAvailableError,
    SquadNotConfiguredError,
)


def test_save_squad_ok(db, user):
    """Saves a valid squad"""

    club = Club(nombre="My Club", user_id=user.id)
    db.add(club)
    db.commit()

    players = []
    for i in range(6):
        player = ClubPlayer(
            name=f"Player {i}",
            club_id=club.id,
            strength=50, control=50, precision=50, agility=50, speed=50,
        )
        db.add(player)
        players.append(player)
    db.commit()

    behavior = Behavior(name="Offensive", code="def decidir(contexto):\n    pass")
    db.add(behavior)
    db.commit()

    link = UserBehavior(user_id=user.id, behavior_id=behavior.id)
    db.add(link)
    db.commit()

    squad_input = SquadInput(
        formation="1-2",
        starters=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[0:3]],
        substitutes=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[3:6]],
    )

    result = squads_service.save_squad(db, user, squad_input)

    assert result.formation == "1-2"
    assert len(result.members) == 6
    starters = [m for m in result.members if m.is_starter]
    substitutes = [m for m in result.members if not m.is_starter]
    assert len(starters) == 3
    assert len(substitutes) == 3


def test_save_squad_invalid_formation(db, user):
    """Invalid formation raises InvalidFormationError"""

    club = Club(nombre="My Club", user_id=user.id)
    db.add(club)
    db.commit()

    squad_input = SquadInput(
        formation="made-up-formation",
        starters=[SquadMemberInput(club_player_id="a", behavior_id=1)] * 3,
        substitutes=[SquadMemberInput(club_player_id="b", behavior_id=1)] * 3,
    )

    with pytest.raises(InvalidFormationError):
        squads_service.save_squad(db, user, squad_input)


def test_save_squad_not_enough_players(db, user):
    """Club with fewer than 6 players raises InsufficientPlayersError"""

    club = Club(nombre="My Club", user_id=user.id)
    db.add(club)
    db.commit()

    # Only 2 players, not enough
    for i in range(2):
        db.add(ClubPlayer(
            name=f"Player {i}", club_id=club.id,
            strength=50, control=50, precision=50, agility=50, speed=50,
        ))
    db.commit()

    squad_input = SquadInput(
        formation="1-2",
        starters=[SquadMemberInput(club_player_id="x", behavior_id=1)] * 3,
        substitutes=[SquadMemberInput(club_player_id="y", behavior_id=1)] * 3,
    )

    with pytest.raises(InsufficientPlayersError):
        squads_service.save_squad(db, user, squad_input)


def test_save_squad_duplicate_players(db, user):
    """The same club_player_id sent twice raises DuplicatePlayersError"""

    club = Club(nombre="My Club", user_id=user.id)
    db.add(club)
    db.commit()

    players = []
    for i in range(6):
        player = ClubPlayer(
            name=f"Player {i}", club_id=club.id,
            strength=50, control=50, precision=50, agility=50, speed=50,
        )
        db.add(player)
        players.append(player)
    db.commit()

    behavior = Behavior(name="Offensive", code="def decidir(contexto):\n    pass")
    db.add(behavior)
    db.commit()
    db.add(UserBehavior(user_id=user.id, behavior_id=behavior.id))
    db.commit()

    squad_input = SquadInput(
        formation="1-2",
        starters=[SquadMemberInput(club_player_id=players[0].id, behavior_id=behavior.id)] * 3,
        substitutes=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[3:6]],
    )

    with pytest.raises(DuplicatePlayersError):
        squads_service.save_squad(db, user, squad_input)


def test_save_squad_player_not_in_club(db, user):
    """A club_player_id that doesn't belong to the club raises PlayerNotInClubError"""

    club = Club(nombre="My Club", user_id=user.id)
    db.add(club)
    db.commit()

    players = []
    for i in range(6):
        player = ClubPlayer(
            name=f"Player {i}", club_id=club.id,
            strength=50, control=50, precision=50, agility=50, speed=50,
        )
        db.add(player)
        players.append(player)
    db.commit()

    behavior = Behavior(name="Offensive", code="def decidir(contexto):\n    pass")
    db.add(behavior)
    db.commit()
    db.add(UserBehavior(user_id=user.id, behavior_id=behavior.id))
    db.commit()

    squad_input = SquadInput(
        formation="1-2",
        starters=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[0:3]],
        substitutes=[
            SquadMemberInput(club_player_id="fake-id-1", behavior_id=behavior.id),
            SquadMemberInput(club_player_id="fake-id-2", behavior_id=behavior.id),
            SquadMemberInput(club_player_id="fake-id-3", behavior_id=behavior.id),
        ],
    )

    with pytest.raises(PlayerNotInClubError):
        squads_service.save_squad(db, user, squad_input)


def test_save_squad_behavior_not_available(db, user):
    """A behavior_id that doesn't belong to the user raises BehaviorNotAvailableError"""

    club = Club(nombre="My Club", user_id=user.id)
    db.add(club)
    db.commit()

    players = []
    for i in range(6):
        player = ClubPlayer(
            name=f"Player {i}", club_id=club.id,
            strength=50, control=50, precision=50, agility=50, speed=50,
        )
        db.add(player)
        players.append(player)
    db.commit()

    # Behavior exists, but it's NOT linked to this user
    behavior = Behavior(name="Offensive", code="def decidir(contexto):\n    pass")
    db.add(behavior)
    db.commit()

    squad_input = SquadInput(
        formation="1-2",
        starters=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[0:3]],
        substitutes=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[3:6]],
    )

    with pytest.raises(BehaviorNotAvailableError):
        squads_service.save_squad(db, user, squad_input)


def test_save_squad_replaces_existing(db, user):
    """Saving a squad twice replaces the previous one, not adds to it"""

    club = Club(nombre="My Club", user_id=user.id)
    db.add(club)
    db.commit()

    players = []
    for i in range(6):
        player = ClubPlayer(
            name=f"Player {i}", club_id=club.id,
            strength=50, control=50, precision=50, agility=50, speed=50,
        )
        db.add(player)
        players.append(player)
    db.commit()

    behavior = Behavior(name="Offensive", code="def decidir(contexto):\n    pass")
    db.add(behavior)
    db.commit()
    db.add(UserBehavior(user_id=user.id, behavior_id=behavior.id))
    db.commit()

    first_input = SquadInput(
        formation="1-2",
        starters=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[0:3]],
        substitutes=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[3:6]],
    )
    squads_service.save_squad(db, user, first_input)

    second_input = SquadInput(
        formation="2-1",
        starters=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[3:6]],
        substitutes=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[0:3]],
    )
    result = squads_service.save_squad(db, user, second_input)

    assert result.formation == "2-1"
    assert len(result.members) == 6


def test_get_squad_not_configured(db, user):
    """SquadNotConfiguredError if the club has no squad yet"""

    club = Club(nombre="My Club", user_id=user.id)
    db.add(club)
    db.commit()

    with pytest.raises(SquadNotConfiguredError):
        squads_service.get_squad(db, user)


def test_get_squad_ok(db, user):
    """Retrieves the saved squad"""

    club = Club(nombre="My Club", user_id=user.id)
    db.add(club)
    db.commit()

    players = []
    for i in range(6):
        player = ClubPlayer(
            name=f"Player {i}", club_id=club.id,
            strength=50, control=50, precision=50, agility=50, speed=50,
        )
        db.add(player)
        players.append(player)
    db.commit()

    behavior = Behavior(name="Offensive", code="def decidir(contexto):\n    pass")
    db.add(behavior)
    db.commit()
    db.add(UserBehavior(user_id=user.id, behavior_id=behavior.id))
    db.commit()

    squad_input = SquadInput(
        formation="1-2",
        starters=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[0:3]],
        substitutes=[SquadMemberInput(club_player_id=p.id, behavior_id=behavior.id) for p in players[3:6]],
    )
    squads_service.save_squad(db, user, squad_input)

    result = squads_service.get_squad(db, user)

    assert result.formation == "1-2"
    assert len(result.members) == 6