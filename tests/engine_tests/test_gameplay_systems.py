import unittest
from engine.ecs.world import World
from engine.components.core import Health, Transform, Inventory
from engine.components.gameplay import Trigger
from engine.systems.lifecycle import DamageSystem
from engine.systems.interaction import InventorySystem, TriggerSystem
from panda3d.core import LVector3f as Vec3

class TestGameplaySystems(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.event_bus = self.world.event_bus

    def test_damage_system(self):
        system = DamageSystem(self.world, self.event_bus)
        self.world.add_system(system)
        
        entity = self.world.create_entity()
        self.world.add_component(entity, Health(current=100, max_hp=100))
        
        # Simulate damage event
        self.event_bus.publish("on_entity_damage", entity_id=entity, amount=10)
        
        # Must pump events if system handles them immediately? 
        # In our implementation, DamageSystem subscribes directly.
        # But publish() is synchronous in our bus.
        
        health = self.world.get_component(entity, Health)
        self.assertEqual(health.current, 90)

    def test_inventory_pickup(self):
        system = InventorySystem(self.world, self.event_bus)
        system.initialize() # Subscribe
        
        player = self.world.create_entity()
        self.world.add_component(player, Inventory(slots=[None]*5))
        
        self.event_bus.publish("on_item_pickup", entity_id=player, item_type="gold")
        
        inv = self.world.get_component(player, Inventory)
        self.assertEqual(inv.slots[0], "gold")

    def test_trigger_system(self):
        system = TriggerSystem(self.world, self.event_bus)
        self.world.add_system(system)
        
        # Zone
        zone = self.world.create_entity()
        self.world.add_component(zone, Transform(position=Vec3(10,0,10)))
        self.world.add_component(zone, Trigger(bounds_min=Vec3(-1,-1,-1), bounds_max=Vec3(1,1,1)))
        
        # Player inside
        player = self.world.create_entity()
        self.world.add_component(player, Transform(position=Vec3(10.5, 0, 10.5)))
        
        # Listen for event
        triggered = []
        self.event_bus.subscribe("on_zone_enter", lambda e: triggered.append(e.zone_id))
        
        system.update(0.1)
        
        self.assertIn(zone, triggered)

if __name__ == '__main__':
    unittest.main()
