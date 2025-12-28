
import asyncio
from unittest.mock import MagicMock, patch
from engine.networking.server import GameServer
from engine.networking.client import GameClient
from engine.core.server_hot_config import ServerHotConfig

class ServerTestHarness:
    """Helper to manage a GameServer instance for testing."""
    def __init__(self):
        self.config = ServerHotConfig()
        self.server = GameServer(self.config)
        self.server.port = 0
        self.task = None
        self.port = 0

    async def start(self):
        """Start the server in a background task."""
        # Monkey patch start_server to capture port
        original_start_server = asyncio.start_server
        
        async def mock_start_server(cb, host, port):
            server_obj = await original_start_server(cb, host, port)
            self.port = server_obj.sockets[0].getsockname()[1]
            return server_obj
            
        self.patcher = patch('asyncio.start_server', side_effect=mock_start_server)
        self.patcher.start()
        
        self.task = asyncio.create_task(self.server.start())
        
        # Wait for startup and port binding
        for _ in range(50): # Wait up to 5s
            if self.port != 0:
                break
            await asyncio.sleep(0.1)
            
        self.patcher.stop()
        
        if self.port == 0:
            raise RuntimeError("Server failed to start and bind port")
                
    async def stop(self):
        """Stop the server."""
        self.server.running = False
        if self.server.server:
            self.server.server.close()
            await self.server.server.wait_closed()
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

class ClientTestHarness:
    """Helper to manage a GameClient instance for testing."""
    def __init__(self):
        self.client = None
        self.receive_task = None
        
    async def connect(self, host: str, port: int):
        self.client = GameClient(host, port)
        # Mock UI callbacks to avoid errors
        self.client.on_player_joined = MagicMock()
        self.client.on_player_left = MagicMock()
        self.client.on_chat_message = MagicMock()
        self.client.on_state_update = MagicMock()
        self.client.update_other_player_pos = MagicMock()
        
        # Set loop for testing
        self.client.loop = asyncio.get_running_loop()
        
        connected = await self.client._connect_with_retry()
            
        if connected:
            self.receive_task = asyncio.create_task(self.client._receive_loop())
        return connected

    async def disconnect(self):
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
            self.receive_task = None
            
        if self.client:
            self.client.disconnect()
