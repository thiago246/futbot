import asyncio

from app.core.ws_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self, fail=False):
        self.accepted = False
        self.sent = []
        self.fail = fail

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        if self.fail:
            raise RuntimeError("conexión caída")
        self.sent.append(message)


def test_connect_accepts_and_adds_to_room():
    manager, ws = ConnectionManager(), FakeWebSocket()
    asyncio.run(manager.connect("league:1", ws))
    assert ws.accepted
    assert manager.rooms["league:1"] == [ws]


def test_broadcast_reaches_only_its_room():
    manager, a, b, other = ConnectionManager(), FakeWebSocket(), FakeWebSocket(), FakeWebSocket()

    async def scenario():
        await manager.connect("league:1", a)
        await manager.connect("league:1", b)
        await manager.connect("league:2", other)
        await manager.broadcast("league:1", {"tipo": "x"})

    asyncio.run(scenario())
    assert a.sent == [{"tipo": "x"}] and b.sent == [{"tipo": "x"}]
    assert other.sent == []


def test_broadcast_to_unknown_room_does_nothing():
    asyncio.run(ConnectionManager().broadcast("nadie", {"tipo": "x"}))


def test_disconnect_removes_and_deletes_empty_room():
    manager, ws = ConnectionManager(), FakeWebSocket()
    asyncio.run(manager.connect("league:1", ws))
    manager.disconnect("league:1", ws)
    assert "league:1" not in manager.rooms


def test_disconnect_is_idempotent():
    manager, ws = ConnectionManager(), FakeWebSocket()
    manager.disconnect("league:1", ws)  # sala inexistente
    asyncio.run(manager.connect("league:1", ws))
    manager.disconnect("league:1", ws)
    manager.disconnect("league:1", ws)  # ya no está


def test_broadcast_drops_broken_connection_and_keeps_going():
    manager, broken, healthy = ConnectionManager(), FakeWebSocket(fail=True), FakeWebSocket()

    async def scenario():
        await manager.connect("league:1", broken)
        await manager.connect("league:1", healthy)
        await manager.broadcast("league:1", {"tipo": "x"})

    asyncio.run(scenario())
    assert healthy.sent == [{"tipo": "x"}]
    assert manager.rooms["league:1"] == [healthy]
