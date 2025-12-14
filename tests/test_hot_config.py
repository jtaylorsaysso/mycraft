
import unittest
import json
import tempfile
import time
from pathlib import Path
from util.hot_config import HotConfig

class TestHotConfig(unittest.TestCase):
    def setUp(self):
        # Create a temp file for config
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / "test_config.json"
        
        # Initial config content
        self.initial_data = {
            "movement_speed": 10.0,
            "jump_height": 5.0,
            "god_mode": True
        }
        with open(self.config_path, 'w') as f:
            json.dump(self.initial_data, f)
            
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_defaults(self):
        """Test default values are used when file doesn't exist."""
        # Point to non-existent file
        no_file_path = Path(self.temp_dir.name) / "missing.json"
        config = HotConfig(no_file_path)
        
        # Should have defaults
        self.assertEqual(config.get("movement_speed"), 6.0) # Default
        self.assertEqual(config.get("jump_height"), 3.5) # Default

    def test_load_from_file(self):
        """Test loading values from existing file."""
        config = HotConfig(self.config_path)
        
        self.assertEqual(config.get("movement_speed"), 10.0)
        self.assertEqual(config.get("jump_height"), 5.0)
        self.assertTrue(config.get("god_mode"))
        # Missing value should fallback to default
        self.assertEqual(config.get("gravity"), -12.0)

    def test_update_callback(self):
        """Test callbacks are triggered when file changes."""
        config = HotConfig(self.config_path, check_interval=0.1)
        
        # Capture callback data
        changes = {}
        def on_change(key, val):
            changes[key] = val
        config.on_change(on_change)
        
        # Modify file
        new_data = self.initial_data.copy()
        new_data["movement_speed"] = 20.0
        
        # Wait a bit to ensure mtime changes (some systems have coarse resolution)
        time.sleep(0.1) 
        
        with open(self.config_path, 'w') as f:
            json.dump(new_data, f)
            
        # Trigger update check explicitly to avoid waiting in test
        # (Though update() normally runs on timer, we can force it)
        config.update()
        
        self.assertIn("movement_speed", changes)
        self.assertEqual(changes["movement_speed"], 20.0)

    def test_set_value(self):
        """Test programmatic setting of values."""
        config = HotConfig(self.config_path)
        
        # Capture callback
        changes = {}
        config.on_change(lambda k, v: changes.update({k: v}))
        
        config.set("fov", 110)
        
        self.assertEqual(config.get("fov"), 110)
        self.assertEqual(changes["fov"], 110)

    def test_save(self):
        """Test saving configuration back to file."""
        config = HotConfig(self.config_path)
        config.set("movement_speed", 15.0)
        config.save()
        
        # Read file back
        with open(self.config_path, 'r') as f:
            data = json.load(f)
            
        self.assertEqual(data["movement_speed"], 15.0)

if __name__ == '__main__':
    unittest.main()
