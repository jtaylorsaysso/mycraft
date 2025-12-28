"""Unit tests for ParrySystem."""

import unittest
from engine.ecs.world import World
from engine.components.core import Stamina, Health, CombatState
from games.voxel_world.systems.parry_system import ParrySystem


class MockEvent:
    """Mock event for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestParrySystem(unittest.TestCase):
    """Test parry mechanics with damage mitigation and stamina costs."""
    
    def setUp(self):
        """Set up test world and system."""
        self.world = World()
        self.system = ParrySystem(self.world, self.world.event_bus)
        self.system.initialize()
    
    def test_perfect_parry_stamina_cost(self):
        """Test that perfect parry costs 5 stamina."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, CombatState())
        
        # Trigger parry
        event = MockEvent(entity_id=entity)
        self.system.on_parry_input(event)
        
        # Should have consumed 5 stamina (perfect timing)
        self.assertEqual(stamina.current, 95.0)
        self.assertEqual(stamina.regen_timer, 0.5)  # Delay reset
    
    def test_parry_creates_active_window(self):
        """Test that parry creates an active mitigation window."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, CombatState())
        
        # Trigger parry
        event = MockEvent(entity_id=entity)
        self.system.on_parry_input(event)
        
        # Should have active parry
        self.assertIn(entity, self.system.active_parries)
        _, mitigation = self.system.active_parries[entity]
        self.assertEqual(mitigation, 1.0)  # Perfect = 100% mitigation
    
    def test_perfect_parry_mitigation(self):
        """Test that perfect parry blocks 100% damage."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, CombatState())
        
        # Activate parry
        self.system.on_parry_input(MockEvent(entity_id=entity))
        
        # Simulate incoming damage
        damage_event = MockEvent(target_id=entity, damage=50.0)
        self.system.on_damage_before_system(damage_event)
        
        # Damage should be fully mitigated
        self.assertAlmostEqual(damage_event.damage, 0.0, places=2)
    
    def test_parry_consumed_on_hit(self):
        """Test that parry is consumed after blocking one hit."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, CombatState())
        
        # Activate parry
        self.system.on_parry_input(MockEvent(entity_id=entity))
        self.assertIn(entity, self.system.active_parries)
        
        # Take damage
        damage_event = MockEvent(target_id=entity, damage=50.0)
        self.system.on_damage_before_system(damage_event)
        
        # Parry should be consumed
        self.assertNotIn(entity, self.system.active_parries)
    
    def test_parry_window_expiration(self):
        """Test that parry window expires after 0.15 seconds."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, CombatState())
        
        # Initialize time
        self.system._accumulated_time = 0.0
        
        # Activate parry at time 0
        self.system.on_parry_input(MockEvent(entity_id=entity))
        self.assertIn(entity, self.system.active_parries)
        
        # Advance time to 0.1s (still active)
        self.system._accumulated_time = 0.1
        self.system.update(0.0)
        self.assertIn(entity, self.system.active_parries)
        
        # Advance time to 0.2s (expired)
        self.system._accumulated_time = 0.2
        self.system.update(0.0)
        self.assertNotIn(entity, self.system.active_parries)
    
    def test_insufficient_stamina_blocks_parry(self):
        """Test that parry fails with insufficient stamina."""
        entity = self.world.create_entity()
        stamina = Stamina(current=3.0, max_stamina=100.0)  # Too low
        self.world.add_component(entity, stamina)
        
        # Try to parry
        event = MockEvent(entity_id=entity)
        self.system.on_parry_input(event)
        
        # Should NOT have parried
        self.assertEqual(stamina.current, 3.0)  # Unchanged
        self.assertNotIn(entity, self.system.active_parries)
    
    def test_parry_event_published(self):
        """Test that parry_executed event is published."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, CombatState())
        
        # Subscribe to parry_executed event
        events = []
        self.world.event_bus.subscribe("parry_executed", lambda e: events.append(e))
        
        # Trigger parry
        event = MockEvent(entity_id=entity)
        self.system.on_parry_input(event)
        
        # Should have published event
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].entity_id, entity)
        self.assertEqual(events[0].timing_quality, "perfect")
        self.assertEqual(events[0].mitigation, 1.0)
    
    def test_parry_success_event_published(self):
        """Test that parry_success event is published on damage mitigation."""
        entity = self.world.create_entity()
        stamina = Stamina(current=100.0, max_stamina=100.0)
        self.world.add_component(entity, stamina)
        self.world.add_component(entity, CombatState())
        
        # Subscribe to parry_success event
        events = []
        self.world.event_bus.subscribe("parry_success", lambda e: events.append(e))
        
        # Activate parry
        self.system.on_parry_input(MockEvent(entity_id=entity))
        
        # Take damage
        damage_event = MockEvent(target_id=entity, damage=50.0)
        self.system.on_damage_before_system(damage_event)
        
        # Should have published success event
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].entity_id, entity)
        self.assertEqual(events[0].original_damage, 50.0)
        self.assertAlmostEqual(events[0].mitigated_damage, 0.0, places=2)


if __name__ == '__main__':
    unittest.main()
