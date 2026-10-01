from sqlalchemy.orm import Session
from app.models.league import League, LeagueMember
from app.models.club import Club
from app.schemas.league import LeagueCreateSchema, LeagueLobbyOut, LobbyClubSchema
from app.core.exceptions import (MinTeamsTooLowError, EmptyLeaguePasswordError,
                                InvalidLeaguePasswordError, LeagueFullError,
                                LeagueAlreadyStartedError, AlreadyInLeagueError, 
                                LeagueNotFoundError, NotInLeagueError, AlreadyPlayedMatchesError)
from app.core.security import hash_password, verify_password


def create_league(db: Session, user_id: str, data: LeagueCreateSchema) -> League:
    if data.minEquipos < 3:
        raise MinTeamsTooLowError()
    if data.esPrivada and not data.password:
        raise EmptyLeaguePasswordError()

    league = League(
        nombre=data.nombre,
        is_private=data.esPrivada,
        password_hash=hash_password(data.password) if data.esPrivada else None,
        min_teams=data.minEquipos,
        max_teams=data.maxEquipos,
        match_duration=data.duracionPartido,
        creator_id=user_id,
    )
    db.add(league)
    db.commit()
    db.refresh(league)
    return league


def list_leagues(db: Session, page: int, page_size: int) -> dict:
    query = db.query(League)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "page": page, "pageSize": page_size, "total": total}


def join_league(db: Session, user_id: str, league_id: str, password: str | None) -> None:
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise LeagueNotFoundError()

    if league.status == "en_curso" or league.status == "finalizada":
        raise LeagueAlreadyStartedError()

    club = db.query(Club).filter(Club.user_id == user_id).first()

    already_member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.club_id == club.id,
    ).first()
    if already_member:
        raise AlreadyInLeagueError()

    member_count = db.query(LeagueMember).filter(LeagueMember.league_id == league_id).count()
    if member_count >= league.max_teams:
        raise LeagueFullError()

    if league.is_private:
        if not password or not verify_password(password, league.password_hash):
            raise InvalidLeaguePasswordError()

    member = LeagueMember(league_id=league_id, club_id=club.id)
    db.add(member)

    if member_count + 1 >= league.max_teams:
        league.status = "en_curso"

    db.commit()

def get_league(db: Session, league_id: str) -> League:
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise LeagueNotFoundError()
    return league

def leave_league(db: Session, user_id: str, league_id: str) -> None:
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise LeagueNotFoundError()

    club = db.query(Club).filter(Club.user_id == user_id).first()

    member = db.query(LeagueMember).filter(
        LeagueMember.league_id == league_id,
        LeagueMember.club_id == club.id,
    ).first()
    if not member:
        raise NotInLeagueError()

    if member.matches_played > 0:
        raise AlreadyPlayedMatchesError()

    db.delete(member)

    if league.status == "en_curso":
        league.status = "esperando_equipos"

    db.commit()



def get_lobby(db: Session, league_id: str) -> LeagueLobbyOut:
    """Lobby de espera: la liga, los inscriptos y los cupos que quedan."""
    league = db.query(League).filter(League.id == league_id).first()
    if not league:
        raise LeagueNotFoundError()

    clubs = (
        db.query(Club)
        .join(LeagueMember, LeagueMember.club_id == Club.id)
        .filter(LeagueMember.league_id == league_id)
        .order_by(Club.nombre)
        .all()
    )
    current = len(clubs)
    return LeagueLobbyOut(
        id=league.id,
        nombre=league.nombre,
        estado=league.status,
        minEquipos=league.min_teams,
        maxEquipos=league.max_teams,
        equiposActuales=current,
        cuposRestantes=max(league.max_teams - current, 0),
        listaParaIniciar=current >= league.min_teams,
        equipos=[LobbyClubSchema(clubId=c.id, nombre=c.nombre) for c in clubs],
    )