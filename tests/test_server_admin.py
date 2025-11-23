import asyncio
import json

from network.server import GameServer


class FakeWriter:
    def __init__(self):
        self.buffer = b""
        self.closed = False

    def write(self, data: bytes) -> None:
        self.buffer += data

    async def drain(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        pass


def _decode_single_message(writer: FakeWriter):
    data = writer.buffer.decode("utf-8").strip()
    assert data, "no data written to fake writer"
    return json.loads(data)


def test_admin_list_includes_host_and_player():
    server = GameServer()
    writer = FakeWriter()
    player_id = "player_1"

    # Register a fake client and player state
    server.clients[player_id] = writer
    server.player_states[player_id] = {
        "pos": [0, 0, 0],
        "rot_y": 0,
        "last_update": 0.0,
    }

    async def run():
        await server.handle_admin_command(player_id, "/list")

    asyncio.run(run())

    message = _decode_single_message(writer)
    assert message["type"] == "admin_response"
    lines = message["lines"]
    assert any("host_player" in line for line in lines)
    assert any("player_1" in line for line in lines)


def test_admin_hostpos_and_hostrot_update_host_state():
    server = GameServer()
    writer = FakeWriter()
    player_id = "player_1"

    server.clients[player_id] = writer
    server.player_states[player_id] = {
        "pos": [0, 0, 0],
        "rot_y": 0,
        "last_update": 0.0,
    }

    async def run():
        await server.handle_admin_command(player_id, "/hostpos 1 2 3")
        await server.handle_admin_command(player_id, "/hostrot 45")

    asyncio.run(run())

    host_state = server.player_states[server.host_player_id]
    assert host_state["pos"] == [1.0, 2.0, 3.0]
    assert host_state["rot_y"] == 45.0


def test_admin_kick_removes_client_and_state():
    server = GameServer()
    writer = FakeWriter()
    player_id = "player_1"

    server.clients[player_id] = writer
    server.player_states[player_id] = {
        "pos": [0, 0, 0],
        "rot_y": 0,
        "last_update": 0.0,
    }

    async def run():
        await server.handle_admin_command(player_id, "/kick player_1")

    asyncio.run(run())

    assert player_id not in server.clients
    assert player_id not in server.player_states
