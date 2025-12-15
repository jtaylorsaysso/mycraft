
import unittest
import asyncio
import logging
from unittest.mock import MagicMock, patch

from tests.test_utils.integration_harness import TestServerWrapper, TestClientWrapper



class TestIntegrationMultiplayer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Configure logging to avoid noise
        logging.getLogger("net.server").setLevel(logging.WARNING)
        logging.getLogger("net.client").setLevel(logging.WARNING)
        
        self.test_server = TestServerWrapper()
        await self.test_server.start()
        
    async def asyncTearDown(self):
        await self.test_server.stop()
        
    async def test_client_server_connection_flow(self):
        """Verify a client can connect and receive welcome message."""
        client = TestClientWrapper()
        
        # Connect
        connected = await client.connect("127.0.0.1", self.test_server.port)
        self.assertTrue(connected, "Client failed to connect")
        
        # Check if server sees the client
        self.assertEqual(len(self.test_server.server.clients), 1)
        
        await client.disconnect()

    async def test_two_players_see_each_other(self):
        """Verify that when a second player joins, both are notified."""
        client1 = TestClientWrapper()
        client2 = TestClientWrapper()
        
        await client1.connect("127.0.0.1", self.test_server.port)
        await asyncio.sleep(0.1)
        
        await client2.connect("127.0.0.1", self.test_server.port)
        await asyncio.sleep(0.5) # Wait for propagation
        
        # Client 1 should see Client 2 join
        self.assertTrue(client1.client.on_player_joined.called)
        
        await client1.disconnect()
        await client2.disconnect()

        client = TestClientWrapper()
        connected = await client.connect("127.0.0.1", self.test_server.port)
        self.assertTrue(connected, "Client failed to connect")
        
        # Send a chat message
        msg = {
            "type": "chat",
            "message": "Hello World",
            "player_id": client.client.player_id
        }
        await client.client.send_message(msg)
        
        # Allow time for roundtrip
        await asyncio.sleep(0.2)
        
        # Check mock
        self.assertTrue(client.client.on_chat_message.called)
        
        await client.disconnect()

