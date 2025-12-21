import unittest
import asyncio
import threading
import time
import socket
import json
from engine.networking.server import GameServer
from engine.core.server_hot_config import ServerHotConfig

class MockConfig(ServerHotConfig):
    def __init__(self):
        self.config = {"port": 5422, "broadcast_rate": 20, "max_players": 32, "debug": True}
        self.observers = []
    def get(self, key, default=None):
        return self.config.get(key, default)
    def on_change(self, callback):
        pass
    async def update_loop(self):
        pass

class TestNetworkStress(unittest.TestCase):
    def setUp(self):
        # Use a non-standard port to avoid conflict
        self.port = 5422
        self.config = MockConfig()
        self.server = GameServer(self.config)
        self.server.port = self.port  # Ensure port match
        
        # Start server in thread
        self.loop = asyncio.new_event_loop()
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        time.sleep(1.0) # Wait for server start
        
    def _run_server(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.server.start())

    def tearDown(self):
        self.server.running = False
        if self.server.server:
            self.server.server.close()
        # Allow cleanup
        time.sleep(0.5)

    def test_rapid_connect_disconnect(self):
        """Test quickly connecting and disconnecting many times."""
        print("\n[Stress] Rapid connect/disconnect...")
        
        async def run_single_cycle(i):
            try:
                reader, writer = await asyncio.open_connection('127.0.0.1', self.port)
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                return f"Connect failed at cycle {i}: {e}"
            return None

        async def run_cycles():
            for i in range(20):
                err = await run_single_cycle(i)
                if err:
                    return err
            return None
            
        error = asyncio.run(run_cycles())
        if error:
            self.fail(error)
        
        # Give server a moment to cleanup
        time.sleep(1.0)
        
        # Check server state
        self.assertEqual(len(self.server.clients), 0, f"Server leaked clients: {len(self.server.clients)}")

    def test_concurrent_clients(self):
        """Test multiple simultaneous clients."""
        print("\n[Stress] Concurrent clients...")
        n_clients = 10
        
        async def client_lifecycle():
            try:
                reader, writer = await asyncio.open_connection('127.0.0.1', self.port)
                # Read welcome
                data = await reader.readline()
                msg = json.loads(data.decode())
                if msg['type'] != 'welcome':
                    return "Wrong message"
                return writer
            except Exception as e:
                print(f"Client connect failed: {e}")
                return None

        async def run_test():
            # Concurrently connect all
            tasks = [client_lifecycle() for _ in range(n_clients)]
            writers = await asyncio.gather(*tasks)
            writers = [w for w in writers if w]
            
            if len(writers) != n_clients:
                return f"Only {len(writers)}/{n_clients} connected"
                
            # Wait a bit to ensure server registered them
            await asyncio.sleep(0.5)
            
            # Since we can't easily check server.clients (in another thread) safely from here 
            # without race conditions, we'll verify connections stay open.
            
            # Close all
            for w in writers:
                w.close()
                await w.wait_closed()
                
            return None

        error = asyncio.run(run_test())
        if error:
            self.fail(error)
            
        time.sleep(0.5)
        self.assertEqual(len(self.server.clients), 0, "Server count mismatch after cleanup")

if __name__ == '__main__':
    unittest.main()
