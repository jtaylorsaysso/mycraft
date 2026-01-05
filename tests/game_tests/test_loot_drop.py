"""
Automated verification for Loot Drop Logic.
"""
import unittest
from engine.ecs.world import World
from engine.ecs.events import EventBus
from engine.components.core import Transform, Health
from engine.components.loot import LootComponent, PickupComponent
from engine.components.avatar_colors import AvatarColors
from games.voxel_world.systems.health_system import HealthSystem
from games.voxel_world.systems.loot_system import LootSystem
from panda3d.core import LVector3f

class TestLootDrop(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.event_bus = EventBus()
        self.world.event_bus = self.event_bus
        
        # Systems
        self.health_sys = HealthSystem(self.world, self.event_bus)
        self.loot_sys = LootSystem(self.world, self.event_bus)
        self.health_sys.initialize()
        self.loot_sys.initialize()
        
    def test_enemy_drop(self):
        """Verify killing an enemy drops a color swatch."""
        # Create Enemy
        enemy = self.world.create_entity()
        self.world.add_component(enemy, Transform(position=LVector3f(10, 0, 10)))
        self.world.add_component(enemy, Health(current=10, max_hp=10))
        self.world.add_component(enemy, LootComponent(color_name="red"))
        
        # Kill it (Apply 100 damage)
        self.event_bus.publish("on_entity_damage", target_id=enemy, damage=100.0)
        
        # Check if enemy destroyed (access private dict for verification)
        self.assertFalse(enemy in self.world._entities, "Enemy should be destroyed")
        
        # Check if loot spawned
        pickups = self.world.get_entities_with(PickupComponent, Transform) # API change: get_entities_with works
        self.assertEqual(len(pickups), 1, "Should spawn 1 pickup")
        
        # get_entities_with return set of IDs
        pickup_id = list(pickups)[0]
        pickup = self.world.get_component(pickup_id, PickupComponent)
        self.assertEqual(pickup.color_name, "red", "Pickup should be red")
        
        transform = self.world.get_component(pickup_id, Transform)
        self.assertEqual(transform.position, LVector3f(10, 0, 10), "Pickup should be at death location")
        
    def test_pickup_mechanic(self):
        """Verify picking up unlock color."""
        # Create Player
        player = self.world.create_entity()
        self.world.register_tag(player, "player") # Correct method
        self.world.add_component(player, Transform(position=LVector3f(0, 0, 0)))
        colors = AvatarColors()
        colors.unlocked_colors = ["blue"] # Has blue, needs red
        self.world.add_component(player, colors)
        
        # Create Pickup at player location
        pickup = self.world.create_entity()
        self.world.add_component(pickup, Transform(position=LVector3f(0.5, 0, 0))) # Close enough
        self.world.add_component(pickup, PickupComponent(color_name="red", pickup_radius=1.0))
        
        # Run LootSystem update
        self.loot_sys.update(0.1)
        
        # Verify unlocked
        self.assertIn("red", colors.unlocked_colors, "Player should unlock red")
        self.assertFalse(pickup in self.world._entities, "Pickup should be destroyed")

if __name__ == '__main__':
    unittest.main()
