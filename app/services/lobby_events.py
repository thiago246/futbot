"""Eventos en vivo del lobby de una liga (REQ 10).

Este módulo solo ARMA los mensajes y los PROGRAMA para enviarse; no toca la base de datos.
Los routers lo llaman después de que la operación (unirse, abandonar, cancelar) salió bien.

Todos los mensajes van a la sala "league:{league_id}" del ConnectionManager, y usan el
campo "tipo" igual que el contrato AsyncAPI de partido en vivo.
"""
from fastapi import BackgroundTasks

from app.core.ws_manager import manager
from app.schemas.league import LeagueLobbyOut


def lobby_room(league_id: str) -> str:
    return f"league:{league_id}"


def _capacity(lobby: LeagueLobbyOut) -> dict:
    return {
        "equiposActuales": lobby.equiposActuales,
        "maxEquipos": lobby.maxEquipos,
        "cuposRestantes": lobby.cuposRestantes,
    }


def team_joined_event(lobby: LeagueLobbyOut, club_id: str, club_name: str) -> dict:
    return {"tipo": "equipo_unido", "clubId": club_id, "clubNombre": club_name, **_capacity(lobby)}


def team_left_event(lobby: LeagueLobbyOut, club_id: str, club_name: str) -> dict:
    return {"tipo": "equipo_abandono", "clubId": club_id, "clubNombre": club_name, **_capacity(lobby)}


def ready_to_start_event(lobby: LeagueLobbyOut) -> dict:
    return {
        "tipo": "liga_lista_para_iniciar",
        "equiposActuales": lobby.equiposActuales,
        "minEquipos": lobby.minEquipos,
    }


def league_cancelled_event(league_id: str) -> dict:
    return {"tipo": "liga_cancelada", "ligaId": league_id}


def events_on_join(lobby: LeagueLobbyOut, club_id: str, club_name: str) -> list[dict]:
    """Estado DESPUES que un equipo se una

    Siempre sale equipo_unido. liga_lista_para_iniciar sale solo cuando este club fue el que
    hizo llegar la liga justo a minEquipos: si ya había el mínimo (o más) no se repite, y si
    alguien abandona y otro se une hasta volver al mínimo, vuelve a salir.
    """
    events = [team_joined_event(lobby, club_id, club_name)]
    if lobby.equiposActuales == lobby.minEquipos:
        events.append(ready_to_start_event(lobby))
    return events


def events_on_leave(lobby: LeagueLobbyOut, club_id: str, club_name: str) -> list[dict]:
    """Estado DESPUÉS de que un equipo abandone."""
    return [team_left_event(lobby, club_id, club_name)]


def schedule_events(background_tasks: BackgroundTasks, league_id: str, events: list[dict]) -> None:
    """Programa el envío para DESPUÉS de responder el request HTTP (no demora al que se unió)."""
    room = lobby_room(league_id)
    for event in events:
        background_tasks.add_task(manager.broadcast, room, event)
