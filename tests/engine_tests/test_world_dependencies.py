"""
Unit tests for World dependency management.
"""
import unittest
from engine.ecs.world import World
from engine.ecs.system import System
from engine.components.core import Transform
from panda3d.core import LVector3f


class DependentSystem(System):
    """Test system that depends on specific entities."""
    
    def __init__(self, world, event_bus, dependencies):
        super().__init__(world, event_bus)
        self._dependencies = dependencies
        self.ready_count = 0
    
    def get_dependencies(self):
        return self._dependencies
    
    def on_ready(self):
        super().on_ready()
        self.ready_count += 1


class TestWorldDependencies(unittest.TestCase):
    """Test World's dependency tracking and management."""
    
    def test_pending_systems_tracked(self):
        """World should track systems waiting for dependencies."""
        world = World()
        system = DependentSystem(world, world.event_bus, ["player"])
        world.add_system(system)
        
        # System should be in pending list
        self.assertIn(system, world._pending_systems)
        self.assertFalse(system.ready)
    
    def test_pending_systems_removed_when_ready(self):
        """System should be removed from pending when dependencies satisfied."""
        world = World()
        system = DependentSystem(world, world.event_bus, ["player"])
        world.add_system(system)
        
        # Create dependency
        world.create_entity(tag="player")
        
        # System should no longer be pending
        self.assertNotIn(system, world._pending_systems)
        self.assertTrue(system.ready)
    
    def test_multiple_systems_same_dependency(self):
        """Multiple systems can depend on the same entity."""
        world = World()
        system1 = DependentSystem(world, world.event_bus, ["player"])
        system2 = DependentSystem(world, world.event_bus, ["player"])
        
        world.add_system(system1)
        world.add_system(system2)
        
        # Both waiting
        self.assertFalse(system1.ready)
        self.assertFalse(system2.ready)
        
        # Create player
        world.create_entity(tag="player")
        
        # Both ready
        self.assertTrue(system1.ready)
        self.assertTrue(system2.ready)
    
    def test_dependencies_checked_on_entity_creation(self):
        """Dependencies should be checked when tagged entity is created."""
        world = World()
        system = DependentSystem(world, world.event_bus, ["player"])
        world.add_system(system)
        
        # Create untagged entity - no effect
        world.create_entity()
        self.assertFalse(system.ready)
        
        # Create tagged entity - triggers check
        world.create_entity(tag="player")
        self.assertTrue(system.ready)
    
    def test_dependencies_checked_during_update(self):
        """Pending systems should be checked during world update."""
        world = World()
        system = DependentSystem(world, world.event_bus, ["player"])
        world.add_system(system)
        
        # System waiting
        self.assertFalse(system.ready)
        
        # Manually add tag (simulating late entity creation)
        player_id = world.create_entity()
        world._tags["player"] = player_id
        
        # Update should check pending systems
        world.update(0.016)
        self.assertTrue(system.ready)
    
    def test_on_ready_called_once(self):
        """on_ready should only be called once per system."""
        world = World()
        system = DependentSystem(world, world.event_bus, ["player"])
        world.add_system(system)
        
        # Create dependency
        world.create_entity(tag="player")
        self.assertEqual(system.ready_count, 1)
        
        # Multiple updates shouldn't call on_ready again
        world.update(0.016)
        world.update(0.016)
        self.assertEqual(system.ready_count, 1)
    
    def test_system_with_no_dependencies_not_pending(self):
        """System with no dependencies should never be in pending list."""
        world = World()
        system = DependentSystem(world, world.event_bus, [])
        world.add_system(system)
        
        self.assertNotIn(system, world._pending_systems)
        self.assertTrue(system.ready)


if __name__ == "__main__":
    unittest.main()
