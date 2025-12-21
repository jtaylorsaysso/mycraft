import unittest
from engine.core.config_loader import load_game_config
from engine.game import VoxelGame, Block
from engine.components.gameplay import Trigger
from engine.components.core import Transform
import os
import yaml
from panda3d.core import LVector3f as Vec3

class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.config_data = {
            "name": "Test Game",
            "blocks": {
                "custom": [
                    {
                        "id": "gold_ore",
                        "texture_tile": [3, 0],
                        "color": "#FFD700"
                    }
                ]
            },
            "player": {
                "spawn": [0, 5, 0]
            },
            "entities": [
                {
                    "type": "trigger",
                    "id": "test_zone",
                    "position": [10, 0, 10], 
                    "bounds": [[0,0,0], [10,10,10]]
                }
            ]
        }
        with open("test_config.yaml", "w") as f:
            yaml.dump(self.config_data, f)
            
    def tearDown(self):
        if os.path.exists("test_config.yaml"):
            os.remove("test_config.yaml")

    def test_load_config(self):
        game = load_game_config("test_config.yaml")
        
        self.assertEqual(game.name, "Test Game")
        
        # Check blocks
        self.assertIn("gold_ore", game.blocks)
        self.assertEqual(game.blocks["gold_ore"].color, "#FFD700")
        
        # Check entities
        # Trigger entity
        trigger_id = game.world._tags.get("test_zone")
        self.assertIsNotNone(trigger_id)
        
        trigger = game.world.get_component(trigger_id, Trigger)
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.bounds_max, Vec3(10,10,10))
        
        transform = game.world.get_component(trigger_id, Transform)
        self.assertEqual(transform.position, Vec3(10,0,10))

if __name__ == '__main__':
    unittest.main()
