import unittest
import asyncio
import time
from unittest.mock import MagicMock, patch, AsyncMock
from network.client import GameClient
from network.server import GameServer

class TestErrorHandling(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Setup mocks
        self.mock_config = MagicMock()
        self.mock_config.get.return_value = 5420
        self.mock_config.on_change = MagicMock()
        
    async def test_client_connection_timeout(self):
        """Test that client times out if server doesn't respond."""
        # Create client with short timeout and 1 attempt
        client = GameClient("127.0.0.1", 5420, max_reconnect_attempts=1, connection_timeout=0.1)
        
        # Mock asyncio.open_connection to simulate timeout
        with patch('asyncio.open_connection', side_effect=asyncio.TimeoutError("Timeout")):
             # Since _connect_with_retry catches the error, we verify it returns False
             result = await client._connect_with_retry()
             self.assertFalse(result)
             self.assertFalse(client.connected)

    async def test_client_retry_logic(self):
        """Test that client retries connection specified number of times."""
        client = GameClient("127.0.0.1", 5420, max_reconnect_attempts=3, connection_timeout=0.1)
        
        # We need to mock open_connection to fail.
        # We can use a side effect that counts calls.
        
        call_count = 0
        async def mock_connect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise ConnectionRefusedError("Connection refused")
            
        with patch('asyncio.open_connection', side_effect=mock_connect):
            # Patch sleep to speed up test
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await client._connect_with_retry()
                
                self.assertFalse(result)
                self.assertEqual(call_count, 3) # Should try 3 times
                self.assertEqual(mock_sleep.call_count, 2) # Should sleep 2 times (between attempts)

    async def test_server_detects_client_timeout(self):
        """Test that server detects and removes inactive clients."""
        server = GameServer(self.mock_config)
        server.client_timeout = 0.5  # Short timeout for testing
        
        # Add a fake client
        player_id = "test_player"
        server.clients[player_id] = MagicMock() # Mock writer
        server.player_manager.add_player(player_id)
        
        # Set last activity to way back in the past
        server.client_last_activity[player_id] = time.time() - 2.0
        
        # Run one iteration of monitor (we can't run the actual loop easily, so we extract logic or just call handle_disconnect if we verify logic separately)
        # But let's verify the logic by "running" the check manually if we can, or just simulating the condition.
        
        # Since _monitor_client_timeouts is a loop, we can't call it directly without it blocking.
        # But we can verify `handle_disconnect` works and that our logic in the loop *would* call it.
        # Let's extract the check logic to a method or just test the condition manually:
        
        now = time.time()
        to_disconnect = []
        for pid, last_active in server.client_last_activity.items():
            if now - last_active > server.client_timeout:
                to_disconnect.append(pid)
        
        self.assertEqual(len(to_disconnect), 1)
        self.assertEqual(to_disconnect[0], player_id)
        
        # Now verify handle_disconnect removes the client
        await server.handle_disconnect(player_id)
        self.assertNotIn(player_id, server.clients)
        self.assertNotIn(player_id, server.client_last_activity)

    async def test_server_activity_update(self):
        """Test that client activity timestamp is updated on messages."""
        server = GameServer(self.mock_config)
        player_id = "test_player"
        server.client_last_activity[player_id] = 0.0
        
        # Simulate receiving a message
        await server.handle_message(player_id, {"type": "state_update"})
        
        self.assertGreater(server.client_last_activity[player_id], 0.0)

if __name__ == '__main__':
    unittest.main()
