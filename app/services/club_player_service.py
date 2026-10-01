from sqlalchemy.orm import Session
from app.models.club_player import ClubPlayer
from app.models.club import Club
from app.schemas.club_player import PlayerCreateSchema


def create_player(db: Session, user_id: str, data: PlayerCreateSchema) -> ClubPlayer:
    club = db.query(Club).filter(Club.user_id == user_id).first()
    player = ClubPlayer(
        club_id=club.id,
        name=data.name,
        strength=data.stats.strength,
        control=data.stats.control,
        precision=data.stats.precision,
        agility=data.stats.agility,
        speed=data.stats.speed,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def list_players(db: Session, user_id: str) -> list[ClubPlayer]:
    club = db.query(Club).filter(Club.user_id == user_id).first()
    return db.query(ClubPlayer).filter(ClubPlayer.club_id == club.id).all()