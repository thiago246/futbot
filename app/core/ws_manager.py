"""Administra las conexiones WebSocket abiertas, agrupadas por "sala".

Una sala puede ser un partido ("match:12"), un lobby de liga ("league:3"), etc.
El motor del partido (engine/) usa broadcast() para empujar el estado a todos los que miran.
"""
import asyncio

from fastapi import WebSocket

CLOSE_NORMAL = 1000


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[str, list[WebSocket]] = {}
        # referencias a los cierres programados, para que el GC no los cancele
        self._close_tasks: set[asyncio.Task] = set()

    async def connect(self, room: str, websocket: WebSocket) -> None:
        """Aceptar la conexión y agregarla a la sala."""
        await websocket.accept()
        self.rooms.setdefault(room, []).append(websocket)

    def disconnect(self, room: str, websocket: WebSocket) -> None:
        """Sacar la conexión de la sala. Si esta ya no está, no hace nada.
        Las salas que quedan vacías se eliminan para no acumular memoria."""
        connections = self.rooms.get(room)
        if connections is None:
            return
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            del self.rooms[room]

    async def broadcast(self, room: str, message: dict) -> None:
        """Enviar un JSON a todos los conectados de la sala.

        Si una sala no existe (nadie conectado) no hace nada. Si el envío a un cliente
        falla (se cayó sin avisar), se lo saca de la sala y se sigue con los demás:
        un cliente roto no debe impedir que el resto reciba el mensaje.
        """
        for websocket in list(self.rooms.get(room, [])):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(room, websocket)

    async def close_room(self, room: str, code: int = CLOSE_NORMAL) -> None:
        """Cerrar todas las conexiones de la sala y eliminarla.
        Si cerrar una falla (ya estaba caída), se sigue con las demás."""
        for websocket in self.rooms.pop(room, []):
            try:
                await websocket.close(code=code)
            except Exception:
                pass

    def schedule_close(self, room: str, delay: float) -> asyncio.Task:
        """Programar close_room(room) para dentro de `delay` segundos.
        Hay que llamarla desde dentro de un event loop en marcha."""

        async def _close_later() -> None:
            await asyncio.sleep(delay)
            await self.close_room(room)

        task = asyncio.get_running_loop().create_task(_close_later())
        self._close_tasks.add(task)
        task.add_done_callback(self._close_tasks.discard)
        return task


# Instancia única compartida por toda la app
manager = ConnectionManager()
