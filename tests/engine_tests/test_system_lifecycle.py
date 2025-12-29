"""
Unit tests for System lifecycle and dependency management.
"""
import unittest
from unittest.mock import MagicMock
from engine.ecs.world import World
from engine.ecs.system import System
from engine.ecs.events import EventBus


class MockSystem(System):
    """Test system with configurable dependencies."""
    
    def __init__(self, world, event_bus, dependencies=None):
        super().__init__(world, event_bus)
        self._dependencies = dependencies or []
        self.initialize_called = False
        self.on_ready_called = False
        self.update_count = 0
    
    def get_dependencies(self):
        return self._dependencies
    
    def initialize(self):
        self.initialize_called = True
    
    def on_ready(self):
        super().on_ready()
        self.on_ready_called = True
    
    def update(self, dt: float):
        self.update_count += 1


class TestSystemLifecycle(unittest.TestCase):
    """Test the three-phase system lifecycle."""
    
    def test_system_starts_not_ready(self):
        """System should start with ready=False."""
        world = World()
        system = MockSystem(world, world.event_bus)
        self.assertFalse(system.ready)
    
    def test_get_dependencies_default(self):
        """Default get_dependencies should return empty list."""
        world = World()
        system = System(world, world.event_bus)
        self.assertEqual(system.get_dependencies(), [])
    
    def test_on_ready_sets_ready_flag(self):
        """on_ready should set ready=True."""
        world = World()
        system = MockSystem(world, world.event_bus)
        self.assertFalse(system.ready)
        system.on_ready()
        self.assertTrue(system.ready)
    
    def test_system_no_dependencies_ready_immediately(self):
        """System with no dependencies should become ready immediately."""
        world = World()
        system = MockSystem(world, world.event_bus, dependencies=[])
        world.add_system(system)
        
        self.assertTrue(system.initialize_called)
        self.assertTrue(system.on_ready_called)
        self.assertTrue(system.ready)
    
    def test_system_with_dependencies_waits(self):
        """System with dependencies should wait until satisfied."""
        world = World()
        system = MockSystem(world, world.event_bus, dependencies=["player"])
        world.add_system(system)
        
        self.assertTrue(system.initialize_called)
        self.assertFalse(system.on_ready_called)
        self.assertFalse(system.ready)
    
    def test_system_ready_when_dependency_created(self):
        """System should become ready when dependency entity is created."""
        world = World()
        system = MockSystem(world, world.event_bus, dependencies=["player"])
        world.add_system(system)
        
        # System waiting
        self.assertFalse(system.ready)
        
        # Create player entity
        world.create_entity(tag="player")
        
        # System should now be ready
        self.assertTrue(system.on_ready_called)
        self.assertTrue(system.ready)
    
    def test_multiple_dependencies(self):
        """System should wait for all dependencies."""
        world = World()
        system = MockSystem(world, world.event_bus, dependencies=["player", "camera"])
        world.add_system(system)
        
        # Create only one dependency
        world.create_entity(tag="player")
        self.assertFalse(system.ready)
        
        # Create second dependency
        world.create_entity(tag="camera")
        self.assertTrue(system.ready)
    
    def test_update_only_called_when_ready(self):
        """System.update should only be called when ready=True."""
        world = World()
        system = MockSystem(world, world.event_bus, dependencies=["player"])
        world.add_system(system)
        
        # Update while not ready
        world.update(0.016)
        self.assertEqual(system.update_count, 0)
        
        # Create dependency
        world.create_entity(tag="player")
        
        # Update when ready
        world.update(0.016)
        self.assertEqual(system.update_count, 1)
    
    def test_disabled_system_not_updated(self):
        """Disabled system should not receive updates even if ready."""
        world = World()
        system = MockSystem(world, world.event_bus)
        world.add_system(system)
        
        # System is ready (no dependencies)
        self.assertTrue(system.ready)
        
        # Disable system
        system.enabled = False
        
        # Update should not be called
        world.update(0.016)
        self.assertEqual(system.update_count, 0)
    
    def test_dependency_created_before_system_added(self):
        """System should become ready immediately if dependencies already exist."""
        world = World()
        
        # Create entity first
        world.create_entity(tag="player")
        
        # Add system that depends on it
        system = MockSystem(world, world.event_bus, dependencies=["player"])
        world.add_system(system)
        
        # Should be ready immediately
        self.assertTrue(system.ready)
        self.assertTrue(system.on_ready_called)


if __name__ == "__main__":
    unittest.main()
