
import unittest
import asyncio
import logging
from unittest.mock import MagicMock, patch

from tests.test_utils.integration_harness import ServerTestHarness, ClientTestHarness



class TestIntegrationWorldSync(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        logging.getLogger("net.server").setLevel(logging.WARNING)
        logging.getLogger("net.client").setLevel(logging.WARNING)
        
        self.test_server = ServerTestHarness()
        await self.test_server.start()
        
    async def asyncTearDown(self):
        await self.test_server.stop()



    async def test_chunk_updates_propagate(self):
        """Verify server block updates reach the client."""
        client = ClientTestHarness()
        
        # Attach listener BEFORE connecting
        future = asyncio.get_running_loop().create_future()
        
        def on_update(event_data):
            if not future.done():
                future.set_result(event_data)
        
        await client.connect("127.0.0.1", self.test_server.port)
        client.client.on_block_update = on_update
        
        # Give receive loop time to start processing
        await asyncio.sleep(0.1)
        
        # Server changes a block
        test_pos = (10, 10, 10)
        test_block = "stone"
        
        await self.test_server.server.broadcast_block_update(test_pos, test_block)
        
        # Wait for client to get it
        try:
            result = await asyncio.wait_for(future, timeout=2.0)
            self.assertEqual(tuple(result['position']), test_pos)
            self.assertEqual(result['block_type'], test_block)
        except asyncio.TimeoutError:
            self.fail("Client did not receive block update")
            
        await client.disconnect()


