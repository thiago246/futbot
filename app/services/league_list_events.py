from app.schemas.league import LeagueLobbyOut, LeagueResponseSchema
from fastapi import BackgroundTasks
from app.core.ws_manager import manager


LIST_ROOM = "leagues:list"


def league_created_event(liga: LeagueResponseSchema, total: int) -> dict:
    return {"tipo": "liga_creada", "liga": liga.model_dump(), "total": total}


def league_updated_event(lobby: LeagueLobbyOut) -> dict:
    return {
        "tipo": "liga_actualizada",
        "ligaId": lobby.id,
        "estado": lobby.estado,
        "equiposActuales": lobby.equiposActuales,
        "maxEquipos": lobby.maxEquipos,
        "cuposRestantes": lobby.cuposRestantes,
    }

def schedule_list_event(background_tasks: BackgroundTasks, event: dict) -> None:
    """Avisa a todos los que están viendo la lista de ligas, después de responder el request."""
    background_tasks.add_task(manager.broadcast, LIST_ROOM, event)