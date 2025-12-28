"""Unit tests for StaminaSystem."""

import unittest
from engine.ecs.world import World
from engine.components.core import Stamina
from games.voxel_world.systems.stamina_system import StaminaSystem


class TestStaminaSystem(unittest.TestCase):
    """Test stamina regeneration mechanics."""
    
    def setUp(self):
        """Set up test world and system."""
        self.world = World()
        self.system = StaminaSystem(self.world, self.world.event_bus)
    
    def test_stamina_regeneration_rate(self):
        """Test that stamina regenerates at 20/sec."""
        entity = self.world.create_entity()
        stamina = Stamina(current=50.0, max_stamina=100.0, regen_rate=20.0)
        self.world.add_component(entity, stamina)
        
        # Update for 1 second
        self.system.update(1.0)
        
        # Should have regenerated 20 stamina
        self.assertAlmostEqual(stamina.current, 70.0, places=2)
    
    def test_stamina_regeneration_delay(self):
        """Test that regeneration waits for delay period."""
        entity = self.world.create_entity()
        stamina = Stamina(
            current=50.0,
            max_stamina=100.0,
            regen_rate=20.0,
            regen_delay=0.5,
            regen_timer=0.5  # Delay active
        )
        self.world.add_component(entity, stamina)
        
        # Update for 0.3 seconds (still in delay)
        self.system.update(0.3)
        
        # Should NOT have regenerated yet
        self.assertEqual(stamina.current, 50.0)
        self.assertAlmostEqual(stamina.regen_timer, 0.2, places=2)
        
        # Update for another 0.25 seconds (delay expires, regen starts)
        self.system.update(0.25)
        
        # Timer should be at 0 (or negative, which gets clamped)
        # Stamina should start regenerating immediately after timer hits 0
        # So we should have 0.05s of regen (20 * 0.05 = 1.0)
        self.assertAlmostEqual(stamina.current, 50.0, places=1)  # No regen yet, timer just hit 0
        
        # Update for another 0.1 seconds (now regenerating)
        self.system.update(0.1)
        self.assertAlmostEqual(stamina.current, 52.0, places=1)
    
    def test_stamina_max_cap(self):
        """Test that stamina doesn't exceed max."""
        entity = self.world.create_entity()
        stamina = Stamina(current=95.0, max_stamina=100.0, regen_rate=20.0)
        self.world.add_component(entity, stamina)
        
        # Update for 1 second (would regenerate 20, but capped at 100)
        self.system.update(1.0)
        
        # Should be capped at max
        self.assertEqual(stamina.current, 100.0)
    
    def test_stamina_deduction(self):
        """Test that stamina can be manually deducted."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        self.world.add_component(entity, stamina)
        
        # Deduct stamina (simulating dodge/parry)
        stamina.current -= 25.0
        stamina.regen_timer = stamina.regen_delay  # Reset delay
        
        self.assertEqual(stamina.current, 75.0)
        self.assertEqual(stamina.regen_timer, 0.5)
    
    def test_multiple_entities(self):
        """Test that system handles multiple entities correctly."""
        # Create two entities with different stamina values
        entity1 = self.world.create_entity()
        stamina1 = Stamina(current=50.0, max_stamina=100.0, regen_rate=20.0)
        self.world.add_component(entity1, stamina1)
        
        entity2 = self.world.create_entity()
        stamina2 = Stamina(current=30.0, max_stamina=100.0, regen_rate=20.0)
        self.world.add_component(entity2, stamina2)
        
        # Update for 1 second
        self.system.update(1.0)
        
        # Both should have regenerated
        self.assertAlmostEqual(stamina1.current, 70.0, places=2)
        self.assertAlmostEqual(stamina2.current, 50.0, places=2)


if __name__ == '__main__':
    unittest.main()
