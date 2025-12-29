"""Unit tests for CombatSystem."""

import unittest
from engine.ecs.world import World
from engine.components.core import Transform, Health, CombatState
from engine.physics import KinematicState
from panda3d.core import LVector3f
from games.voxel_world.systems.combat_system import CombatSystem, AttackState


class MockEvent:
    """Mock event for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestCombatSystem(unittest.TestCase):
    """Test combat system with attacks, hit detection, and momentum damage."""
    
    def setUp(self):
        """Set up test world and system."""
        self.world = World()
        self.system = CombatSystem(self.world, self.world.event_bus)
        self.system.initialize()
    
    def test_attack_input_creates_attack_state(self):
        """Test that attack input creates an active attack."""
        entity = self.world.create_entity()
        self.world.add_component(entity, CombatState())
        
        # Trigger attack
        event = MockEvent(entity_id=entity)
        self.system.on_attack_input(event)
        
        # Should have active attack
        self.assertIn(entity, self.system.active_attacks)
        self.assertIsInstance(self.system.active_attacks[entity], AttackState)
    
    def test_cannot_attack_while_attacking(self):
        """Test that player can't start new attack while already attacking."""
        entity = self.world.create_entity()
        self.world.add_component(entity, CombatState())
        
        # First attack
        self.system.on_attack_input(MockEvent(entity_id=entity))
        attack1 = self.system.active_attacks[entity]
        
        # Try second attack
        self.system.on_attack_input(MockEvent(entity_id=entity))
        attack2 = self.system.active_attacks[entity]
        
        # Should be same attack object
        self.assertIs(attack1, attack2)
    
    def test_hit_window_timing(self):
        """Test that hits only register during hit window (0.12-0.18s)."""
        attacker = self.world.create_entity()
        target = self.world.create_entity()
        
        # Setup entities
        self.world.add_component(attacker, Transform(position=LVector3f(0, 0, 0)))
        self.world.add_component(attacker, CombatState())
        self.world.add_component(target, Transform(position=LVector3f(1, 0, 0)))  # 1 unit away
        self.world.add_component(target, Health(current=100, max_hp=100))
        
        # Track damage events
        damage_events = []
        self.world.event_bus.subscribe("on_entity_damage", lambda e: damage_events.append(e))
        
        # Start attack
        self.system.on_attack_input(MockEvent(entity_id=attacker))
        attack = self.system.active_attacks[attacker]
        
        # Before hit window (0.1s)
        attack.elapsed_time = 0.1
        self.system.update(0.0)
        self.assertEqual(len(damage_events), 0)  # No hit yet
        
        # During hit window (0.15s)
        attack.elapsed_time = 0.15
        self.system.update(0.0)
        self.assertEqual(len(damage_events), 1)  # Hit!
        
        # After hit window (0.2s) - shouldn't hit again
        attack.elapsed_time = 0.2
        self.system.update(0.0)
        self.assertEqual(len(damage_events), 1)  # Still only one hit
    
    def test_hit_detection_range(self):
        """Test that hits only register within 2.0 unit range."""
        attacker = self.world.create_entity()
        close_target = self.world.create_entity()
        far_target = self.world.create_entity()
        
        # Setup entities
        self.world.add_component(attacker, Transform(position=LVector3f(0, 0, 0)))
        self.world.add_component(attacker, CombatState())
        self.world.add_component(close_target, Transform(position=LVector3f(1.5, 0, 0)))  # In range
        self.world.add_component(far_target, Transform(position=LVector3f(3.0, 0, 0)))  # Out of range
        self.world.add_component(close_target, Health(current=100, max_hp=100))
        self.world.add_component(far_target, Health(current=100, max_hp=100))
        
        # Track damage events
        damage_events = []
        self.world.event_bus.subscribe("on_entity_damage", lambda e: damage_events.append(e))
        
        # Attack during hit window
        self.system.on_attack_input(MockEvent(entity_id=attacker))
        attack = self.system.active_attacks[attacker]
        attack.elapsed_time = 0.15
        self.system.update(0.0)
        
        # Should only hit close target
        self.assertEqual(len(damage_events), 1)
        self.assertEqual(damage_events[0].target_id, close_target)
    
    def test_momentum_damage_calculation(self):
        """Test that damage = base_damage + velocity_magnitude."""
        attacker = self.world.create_entity()
        target = self.world.create_entity()
        
        # Setup entities with velocity
        self.world.add_component(attacker, Transform(position=LVector3f(0, 0, 0)))
        self.world.add_component(attacker, CombatState())
        self.world.add_component(attacker, KinematicState(
            velocity_x=3.0,
            velocity_y=4.0,
            velocity_z=0.0  # Magnitude = 5.0
        ))
        self.world.add_component(target, Transform(position=LVector3f(1, 0, 0)))
        self.world.add_component(target, Health(current=100, max_hp=100))
        
        # Track damage
        damage_events = []
        self.world.event_bus.subscribe("on_entity_damage", lambda e: damage_events.append(e))
        
        # Attack
        self.system.on_attack_input(MockEvent(entity_id=attacker))
        attack = self.system.active_attacks[attacker]
        attack.elapsed_time = 0.15
        self.system.update(0.0)
        
        # Damage should be 25 (base) + 5 (velocity) = 30
        self.assertEqual(len(damage_events), 1)
        self.assertAlmostEqual(damage_events[0].damage, 30.0, places=1)
    
    def test_one_hit_per_attack(self):
        """Test that each attack can only hit once."""
        attacker = self.world.create_entity()
        target = self.world.create_entity()
        
        # Setup
        self.world.add_component(attacker, Transform(position=LVector3f(0, 0, 0)))
        self.world.add_component(attacker, CombatState())
        self.world.add_component(target, Transform(position=LVector3f(1, 0, 0)))
        self.world.add_component(target, Health(current=100, max_hp=100))
        
        # Track damage
        damage_events = []
        self.world.event_bus.subscribe("on_entity_damage", lambda e: damage_events.append(e))
        
        # Attack
        self.system.on_attack_input(MockEvent(entity_id=attacker))
        attack = self.system.active_attacks[attacker]
        
        # Check multiple times during hit window
        attack.elapsed_time = 0.13
        self.system.update(0.0)
        attack.elapsed_time = 0.15
        self.system.update(0.0)
        attack.elapsed_time = 0.17
        self.system.update(0.0)
        
        # Should only hit once
        self.assertEqual(len(damage_events), 1)
        self.assertTrue(attack.has_hit)
    
    def test_attack_completion(self):
        """Test that attack is removed after 0.5s duration."""
        entity = self.world.create_entity()
        self.world.add_component(entity, CombatState())
        
        # Start attack
        self.system.on_attack_input(MockEvent(entity_id=entity))
        self.assertIn(entity, self.system.active_attacks)
        
        # Advance to completion
        attack = self.system.active_attacks[entity]
        attack.elapsed_time = 0.5
        self.system.update(0.0)
        
        # Should be removed
        self.assertNotIn(entity, self.system.active_attacks)
    
    def test_attack_started_event(self):
        """Test that attack_started event is published."""
        entity = self.world.create_entity()
        self.world.add_component(entity, CombatState())
        
        # Subscribe to event
        events = []
        self.world.event_bus.subscribe("attack_started", lambda e: events.append(e))
        
        # Attack
        self.system.on_attack_input(MockEvent(entity_id=entity))
        
        # Should have published event
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].entity_id, entity)


if __name__ == '__main__':
    unittest.main()
