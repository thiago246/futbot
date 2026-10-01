"""Administra las conexiones WebSocket abiertas, agrupadas por "sala".

Una sala puede ser un partido ("match:12"), un lobby de liga ("league:3"), etc.
El motor del partido (engine/) usa broadcast() para empujar el estado a todos los que miran.
"""
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[str, list[WebSocket]] = {}

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


# Instancia única compartida por toda la app
manager = ConnectionManager()
