import unittest
from unittest.mock import MagicMock
from engine.ecs.world import World
from engine.ecs.events import EventBus
from games.voxel_world.systems.gameplay_input import GameplayInputSystem

class TestGameplayInput(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.event_bus = self.world.event_bus
        self.mock_base = MagicMock()
        self.system = GameplayInputSystem(self.world, self.event_bus, self.mock_base)
        self.system.initialize()

    def test_inventory_toggle(self):
        # Create player
        player = self.world.create_entity(tag="player")
        
        events = []
        self.event_bus.subscribe("toggle_inventory", lambda e: events.append(e))
        
        # Trigger
        self.system._on_inventory()
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].entity_id, player)

    def test_drop_request(self):
        player = self.world.create_entity(tag="player")
        
        events = []
        self.event_bus.subscribe("request_drop_item", lambda e: events.append(e))
        
        self.system._on_drop()
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].entity_id, player)

if __name__ == '__main__':
    unittest.main()
