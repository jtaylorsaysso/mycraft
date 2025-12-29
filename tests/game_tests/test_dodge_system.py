"""Unit tests for DodgeSystem."""

import unittest
from engine.ecs.world import World
from engine.components.core import Stamina, Health, CombatState
from games.voxel_world.systems.dodge_system import DodgeSystem


class MockEvent:
    """Mock event for testing."""
    def __init__(self, entity_id):
        self.entity_id = entity_id


class TestDodgeSystem(unittest.TestCase):
    """Test dodge mechanics with stamina costs and i-frames."""
    
    def setUp(self):
        """Set up test world and system."""
        self.world = World()
        self.system = DodgeSystem(self.world, self.world.event_bus)
        self.system.initialize()
    
    def test_perfect_dodge_stamina_cost(self):
        """Test that perfect dodge costs 15 stamina."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        health = Health(current=100, max_hp=100)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, health)
        self.world.add_component(entity, CombatState())
        
        # Trigger dodge
        event = MockEvent(entity)
        self.system.on_dodge_input(event)
        
        # Should have consumed 15 stamina (perfect timing)
        self.assertEqual(stamina.current, 85.0)
        self.assertEqual(stamina.regen_timer, 0.5)  # Delay reset
    
    def test_dodge_applies_iframes(self):
        """Test that dodge grants invulnerability."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        health = Health(current=100, max_hp=100, invulnerable=False)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, health)
        self.world.add_component(entity, CombatState())
        
        # Trigger dodge
        event = MockEvent(entity)
        self.system.on_dodge_input(event)
        
        # Should be invulnerable
        self.assertTrue(health.invulnerable)
        self.assertIn(entity, self.system.active_dodges)
    
    def test_iframe_duration(self):
        """Test that i-frames expire after 0.3 seconds."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        health = Health(current=100, max_hp=100)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, health)
        self.world.add_component(entity, CombatState())
        
        # Initialize time tracking
        self.system._accumulated_time = 0.0
        
        # Trigger dodge at time 0
        event = MockEvent(entity)
        self.system.on_dodge_input(event)
        
        # Should be invulnerable
        self.assertTrue(health.invulnerable)
        
        # Advance time to 0.2 seconds (still in i-frames)
        self.system._accumulated_time = 0.2
        self.system.update(0.0)  # Just check expiration, don't advance
        self.assertTrue(health.invulnerable)
        
        # Advance time to 0.35 seconds (i-frames expired at 0.3)
        self.system._accumulated_time = 0.35
        self.system.update(0.0)  # Just check expiration
        self.assertFalse(health.invulnerable)
        self.assertNotIn(entity, self.system.active_dodges)
    
    def test_insufficient_stamina_blocks_dodge(self):
        """Test that dodge fails with insufficient stamina."""
        entity = self.world.create_entity()
        stamina = Stamina(current=10.0, max_stamina=100.0)  # Too low
        health = Health(current=100, max_hp=100)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, health)
        self.world.add_component(entity, CombatState())
        
        # Try to dodge
        event = MockEvent(entity)
        self.system.on_dodge_input(event)
        
        # Should NOT have dodged
        self.assertEqual(stamina.current, 10.0)  # Unchanged
        self.assertFalse(health.invulnerable)
        self.assertNotIn(entity, self.system.active_dodges)
    
    def test_dodge_event_published(self):
        """Test that dodge_executed event is published."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        health = Health(current=100, max_hp=100)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, health)
        self.world.add_component(entity, CombatState())
        
        # Subscribe to dodge_executed event
        events = []
        self.world.event_bus.subscribe("dodge_executed", lambda e: events.append(e))
        
        # Trigger dodge
        event = MockEvent(entity)
        self.system.on_dodge_input(event)
        
        # Should have published event
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].entity_id, entity)
        self.assertEqual(events[0].timing_quality, "perfect")
    
    def test_multiple_dodges(self):
        """Test that multiple entities can dodge independently."""
        entity1 = self.world.create_entity()
        stamina1 = Stamina(current=100.0, max_stamina=100.0)
        health1 = Health(current=100, max_hp=100)
        self.world.add_component(entity1, stamina1)
        self.world.add_component(entity1, health1)
        self.world.add_component(entity1, CombatState())
        
        entity2 = self.world.create_entity()
        stamina2 = Stamina(current=100.0, max_stamina=100.0)
        health2 = Health(current=100, max_hp=100)
        self.world.add_component(entity2, stamina2)
        self.world.add_component(entity2, health2)
        self.world.add_component(entity2, CombatState())
        
        # Both dodge
        self.system.on_dodge_input(MockEvent(entity1))
        self.system.on_dodge_input(MockEvent(entity2))
        
        # Both should be invulnerable
        self.assertTrue(health1.invulnerable)
        self.assertTrue(health2.invulnerable)
        self.assertEqual(len(self.system.active_dodges), 2)


if __name__ == '__main__':
    unittest.main()
