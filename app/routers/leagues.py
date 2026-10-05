from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.league import (LeagueCreateSchema, LeagueResponseSchema, PaginatedLeaguesSchema,
                                LeagueJoinSchema, LeagueLobbyOut, LeagueListItemSchema)
from app.services import league_list_events, league_service, lobby_events

router = APIRouter(prefix="/leagues", tags=["Leagues"])


@router.post("", status_code=201, response_model=LeagueResponseSchema)
def create_league(
    data: LeagueCreateSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    league = league_service.create_league(db, current_user.id, data)
    item = LeagueListItemSchema.from_league_count(league, 1)
    total = league_service.count_leagues(db)
    league_list_events.schedule_list_event(background_tasks, league_list_events.league_created_event(item, total))
    return LeagueResponseSchema.from_league(league)


@router.get("", response_model=PaginatedLeaguesSchema)
def list_leagues(
    page: int = Query(default=1),
    pageSize: int = Query(default=20),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = league_service.list_leagues(db, page, pageSize)
    counts = league_service.get_member_counts(db, [l.id for l in result["items"]])
    return PaginatedLeaguesSchema(
        items=[LeagueListItemSchema.from_league_count(l, counts.get(l.id, 0)) for l in result["items"]],
        page=result["page"], pageSize=result["pageSize"], total=result["total"],
    )


@router.post("/{league_id}/join", status_code=200)
def join_league(
    league_id: str,
    background_tasks: BackgroundTasks,
    data: LeagueJoinSchema = LeagueJoinSchema(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    league_service.join_league(db, current_user.id, league_id, data.password)
    lobby = league_service.get_lobby(db, league_id)
    club = current_user.club
    lobby_events.schedule_events(
        background_tasks, league_id, lobby_events.events_on_join(lobby, club.id, club.nombre)
    )
    league_list_events.schedule_list_event(background_tasks, league_list_events.league_updated_event(lobby))  # NUEVO
    return {"message": "Successfully joined the league"}


@router.get("/{league_id}", response_model=LeagueResponseSchema)
def get_league(
    league_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    league = league_service.get_league(db, league_id)
    return LeagueResponseSchema.from_league(league)


@router.post("/{league_id}/leave", status_code=200)
def leave_league(
    league_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    league_service.leave_league(db, current_user.id, league_id)
    lobby = league_service.get_lobby(db, league_id)
    club = current_user.club
    lobby_events.schedule_events(
        background_tasks, league_id, lobby_events.events_on_leave(lobby, club.id, club.nombre)
    )
    league_list_events.schedule_list_event(background_tasks, league_list_events.league_updated_event(lobby))  # NUEVO
    return {"message": "Successfully left the league"}



@router.get("/{league_id}/lobby", response_model=LeagueLobbyOut)
def get_lobby(
    league_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Ver lobby de espera de inicio de liga (estado inicial; los cambios llegan por WS)."""
    return league_service.get_lobby(db, league_id)