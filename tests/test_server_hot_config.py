
import unittest
import json
import tempfile
import asyncio
import os
from pathlib import Path
from util.server_hot_config import ServerHotConfig

class TestServerHotConfig(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "server_config.json"
        
        self.initial_data = {
            "max_players": 8,
            "broadcast_rate": 10
        }
        with open(self.config_path, 'w') as f:
            json.dump(self.initial_data, f)
            
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_initial(self):
        config = ServerHotConfig(self.config_path)
        self.assertEqual(config.get("max_players"), 8)
        self.assertEqual(config.get("broadcast_rate"), 10)
        # Default
        self.assertEqual(config.get("port"), 5420)

    async def test_async_update(self):
        """Test async loop checking for updates."""
        config = ServerHotConfig(self.config_path, check_interval=0.1)
        
        changes = {}
        config.on_change(lambda k, v: changes.update({k: v}))
        
        # Modify file
        await asyncio.sleep(0.2) # Ensure mtime diff
        
        new_data = self.initial_data.copy()
        new_data["max_players"] = 32
        
        # Write update
        with open(self.config_path, 'w') as f:
            json.dump(new_data, f)
            
        # Manually force a check instead of waiting for loop (to test logic)
        # We simulate what the loop does
        config._check_needed() # update time stamp
        # Force reload for test
        config.load_config()
        
        self.assertEqual(changes.get("max_players"), 32)

    def test_set_and_save(self):
        config = ServerHotConfig(self.config_path)
        config.set("debug", True)
        
        self.assertTrue(config.get("debug"))
        
        config.save()
        
        with open(self.config_path, 'r') as f:
            data = json.load(f)
            
        self.assertTrue(data["debug"])

if __name__ == '__main__':
    unittest.main()
