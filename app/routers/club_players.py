from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.club_player import PlayerCreateSchema, PlayerResponseSchema
from app.services import club_player_service

router = APIRouter(prefix="/clubs/me/players", tags=["Players"])


@router.post("", status_code=201, response_model=PlayerResponseSchema)
def create_player(
    data: PlayerCreateSchema,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    player = club_player_service.create_player(db, current_user.id, data)
    return PlayerResponseSchema.from_player(player)


@router.get("", response_model=list[PlayerResponseSchema])
def list_players(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    players = club_player_service.list_players(db, current_user.id)
    return [PlayerResponseSchema.from_player(p) for p in players]