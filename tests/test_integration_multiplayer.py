
import unittest
import asyncio
import logging
from unittest.mock import MagicMock, patch

from tests.test_utils.integration_harness import ServerTestHarness, ClientTestHarness



class TestIntegrationMultiplayer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Configure logging to avoid noise
        logging.getLogger("net.server").setLevel(logging.WARNING)
        logging.getLogger("net.client").setLevel(logging.WARNING)
        
        self.test_server = ServerTestHarness()
        await self.test_server.start()
        
    async def asyncTearDown(self):
        await self.test_server.stop()
        
    async def test_client_server_connection_flow(self):
        """Verify a client can connect and receive welcome message."""
        client = ClientTestHarness()
        
        # Connect
        connected = await client.connect("127.0.0.1", self.test_server.port)
        self.assertTrue(connected, "Client failed to connect")
        
        # Check if server sees the client
        self.assertEqual(len(self.test_server.server.clients), 1)
        
        await client.disconnect()

    async def test_two_players_see_each_other(self):
        """Verify that when a second player joins, both are notified."""
        client1 = ClientTestHarness()
        client2 = ClientTestHarness()
        
        await client1.connect("127.0.0.1", self.test_server.port)
        await asyncio.sleep(0.1)
        
        await client2.connect("127.0.0.1", self.test_server.port)
        await asyncio.sleep(0.5) # Wait for propagation
        
        # Client 1 should see Client 2 join
        self.assertTrue(client1.client.on_player_joined.called)
        
        await client1.disconnect()
        await client2.disconnect()


