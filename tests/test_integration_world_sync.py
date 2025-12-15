
import unittest
import asyncio
import logging
from unittest.mock import MagicMock, patch

from tests.test_utils.integration_harness import TestServerWrapper, TestClientWrapper



class TestIntegrationWorldSync(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        logging.getLogger("net.server").setLevel(logging.WARNING)
        logging.getLogger("net.client").setLevel(logging.WARNING)
        
        self.test_server = TestServerWrapper()
        await self.test_server.start()
        
    async def asyncTearDown(self):
        await self.test_server.stop()



    async def test_chunk_updates_propagate(self):
        """Verify server block updates reach the client."""
        client = TestClientWrapper()
        
        # Setup mock world on client to capture updates
        mock_world = MagicMock()
        client.client = None # Reset so we can set it up before connect
        
        # Manual connect to inject world
        from network.client import GameClient
        
        # We'll use the wrapper's connect for simplicity, but we need to inject mocks *before* receive loop processes messages if possible
        # Wrapper connects then starts loop immediately.
        
        # Let's just mock the callback `on_block_update`
        
        await client.connect("127.0.0.1", self.test_server.port)
        
        # Attach listener
        future = asyncio.get_running_loop().create_future()
        
        def on_update(event_data):
            if not future.done():
                future.set_result(event_data)
                
        client.client.on_block_update = on_update
        
        # Server changes a block
        # We can use the server's command processor or modify chunk directly and broadcast
        # Server doesn't have a direct "set_block_and_broadcast" method easily accessible?
        # CommandProcessor has it.
        
        # Simulate an edit:
        # server.world.set_block(...) -> this is local to server.
        # Server needs to broadcast.
        # server.broadcast_block_update(pos, block_type)
        
        # Let's invoke broadcast directly to verify network path
        test_pos = (10, 10, 10)
        test_block = "stone"
        
        await self.test_server.server.broadcast_block_update(test_pos, test_block)
        
        # Wait for client to get it
        try:
            result = await asyncio.wait_for(future, timeout=1.0)
            self.assertEqual(tuple(result['position']), test_pos)
            self.assertEqual(result['block_type'], test_block)
        except asyncio.TimeoutError:
            self.fail("Client did not receive block update")
            
        await client.disconnect()

