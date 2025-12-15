
import unittest
import asyncio
from tests.test_utils.integration_harness import TestServerWrapper

class TestServerStartup(unittest.IsolatedAsyncioTestCase):
    async def test_server_startup_shutdown(self):
        print("Creating wrapper...")
        wrapper = TestServerWrapper()
        
        print("Starting server...")
        await wrapper.start()
        print(f"Server started on port {wrapper.port}")
        
        self.assertNotEqual(wrapper.port, 0)
        self.assertIsNotNone(wrapper.server.server)
        
        print("Stopping server...")
        await wrapper.stop()
        print("Server stopped.")

if __name__ == '__main__':
    unittest.main()
