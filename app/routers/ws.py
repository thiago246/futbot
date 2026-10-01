"""WebSockets: el servidor empuja datos en vivo al front.

Autenticación: el navegador no puede mandar headers en un WebSocket, así que el token
va por query string:  ws://localhost:8000/ws/matches/5?token=<JWT>

Formato de los mensajes (JSON):  {"type": "state" | "event" | "finished", "data": {...}}
"""
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ALGORITHM, SECRET_KEY
from app.core.ws_manager import manager
from app.models.league import League
from app.models.user import User
from app.services.lobby_events import lobby_room

# Códigos de cierre propios (rango 4000-4999 reservado para aplicaciones)
WS_CLOSE_UNAUTHORIZED = 4401
WS_CLOSE_NOT_FOUND = 4404


def _user_from_token(db: Session, token: str | None) -> User | None:
    """Mismo criterio que get_current_user, pero devuelve None en vez de lanzar excepciones."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    user_id = payload.get("sub")
    return db.get(User, user_id) if user_id else None

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/matches/{match_id}")
async def match_ws(websocket: WebSocket, match_id: int):
    """REQ 16 - Ver el partido en vivo.

    Iría acá:
      1. Validar el token (query param) -> si es inválido, cerrar la conexión.
      2. manager.connect(f"match:{match_id}", websocket)
      3. Mandar de entrada el estado actual del partido.
      4. Mantener la conexión abierta (el MotorDePartido hace el broadcast en cada tick).
      5. En WebSocketDisconnect -> manager.disconnect(...)
    """
    await websocket.accept()
    await websocket.send_json({"type": "error", "data": "Sin implementar: REQ 16"})
    await websocket.close()


@router.websocket("/ws/leagues/{league_id}/lobby")
async def league_lobby_ws(
    websocket: WebSocket,
    league_id: str,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Avisa cuando alguien entra o sale de la liga.

    El servidor solo EMITE (equipo_unido, equipo_abandono, liga_lista_para_iniciar,
    liga_cancelada); los mensajes que mande el cliente se ignoran. Los emiten los routers
    de ligas mediante lobby_events. Sala f"league:{league_id}".

    Si el token es inválido o la liga no existe se cierra la conexión sin aceptarla
    (códigos 4401 / 4404).
    """
    user = _user_from_token(db, token)
    league_exists = user is not None and db.get(League, league_id) is not None
    # Se libera la sesión ya: la conexión puede durar horas y no debe retener la de la DB.
    db.close()

    if user is None:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return
    if not league_exists:
        await websocket.close(code=WS_CLOSE_NOT_FOUND)
        return

    room = lobby_room(league_id)
    await manager.connect(room, websocket)
    try:
        while True:
            await websocket.receive_text()  # solo para detectar la desconexión
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(room, websocket)


@router.websocket("/ws/friendlies/{friendly_id}")
async def friendly_ws(websocket: WebSocket, friendly_id: int):
    """REQ 13/14 (opcional) - Avisa cuando se une alguien al amistoso o cuando arranca el partido.
    Sala f"friendly:{friendly_id}"."""
    await websocket.accept()
    await websocket.send_json({"type": "error", "data": "Sin implementar: REQ 13/14"})
    await websocket.close()