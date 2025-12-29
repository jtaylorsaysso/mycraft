import asyncio
import json

from engine.networking.server import GameServer
from engine.core.server_hot_config import ServerHotConfig


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
    config = ServerHotConfig()
    server = GameServer(config)
    writer = FakeWriter()
    player_id = "player_1"

    # Register a fake client and player state
    server.clients[player_id] = writer
    # Use player manager to add player
    server.player_manager.add_player(player_id)
    # Manually set state if needed, but add_player sets defaults which is fine.

    async def run():
        # Call command processor directly or simulate message? 
        # Simulating message via handle_message is more integration-like but handle_admin_command is what we want to test logic of.
        # But handle_admin_command is gone from server, it's in command_processor.
        # We can call process_command and then send_admin_response manually, OR 
        # use server.handle_message which calls both.
        # Let's use process_command to test logic, and maybe check lines.
        # The original test checked the writer output.
        # server.handle_message will do the writing.
        await server.handle_message(player_id, {"type": "admin_command", "command": "/list"})

    asyncio.run(run())

    message = _decode_single_message(writer)
    assert message["type"] == "admin_response"
    lines = message["lines"]
    assert any("host_player" in line for line in lines)
    assert any("player_1" in line for line in lines)


def test_admin_hostpos_and_hostrot_update_host_state():
    config = ServerHotConfig()
    server = GameServer(config)
    writer = FakeWriter()
    player_id = "player_1"

    server.clients[player_id] = writer
    server.player_manager.add_player(player_id)

    async def run():
        await server.handle_message(player_id, {"type": "admin_command", "command": "/hostpos 1 2 3"})
        await server.handle_message(player_id, {"type": "admin_command", "command": "/hostrot 45"})

    asyncio.run(run())

    host_state = server.player_manager.get_player_state(server.host_player_id)
    assert host_state["pos"] == [1.0, 2.0, 3.0]
    assert host_state["rot_y"] == 45.0


def test_admin_kick_removes_client_and_state():
    config = ServerHotConfig()
    server = GameServer(config)
    writer = FakeWriter()
    player_id = "player_1"

    server.clients[player_id] = writer
    server.player_manager.add_player(player_id)

    async def run():
        await server.handle_message(player_id, {"type": "admin_command", "command": "/kick player_1"})

    asyncio.run(run())

    assert player_id not in server.clients
    assert server.player_manager.get_player_state(player_id) is None
