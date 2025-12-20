import unittest
from engine.ecs.world import World
from engine.ecs.component import Component, register_component
from engine.ecs.system import System
from engine.ecs.events import EventBus
from dataclasses import dataclass

@register_component
@dataclass
class TestComponent(Component):
    value: int = 0

class TestSystem(System):
    def update(self, dt: float):
        for entity in self.world.get_entities_with(TestComponent):
            comp = self.world.get_component(entity, TestComponent)
            comp.value += 1

class TestECSCore(unittest.TestCase):
    def setUp(self):
        self.world = World()

    def test_entity_creation(self):
        entity = self.world.create_entity()
        self.assertIsInstance(entity, str)
        self.assertTrue(len(entity) > 0)
        
    def test_component_assignment(self):
        entity = self.world.create_entity()
        comp = TestComponent(value=10)
        self.world.add_component(entity, comp)
        
        fetched = self.world.get_component(entity, TestComponent)
        self.assertEqual(fetched.value, 10)
        self.assertTrue(self.world.has_component(entity, TestComponent))

    def test_system_update(self):
        entity = self.world.create_entity()
        self.world.add_component(entity, TestComponent(value=0))
        
        system = TestSystem(self.world, self.world.event_bus)
        self.world.add_system(system)
        
        self.world.update(1.0)
        
        comp = self.world.get_component(entity, TestComponent)
        self.assertEqual(comp.value, 1)

    def test_event_bus(self):
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event.data)
            
        bus.subscribe("test_event", handler)
        bus.publish("test_event", data="payload")
        
        self.assertEqual(received, ["payload"])
        
    def test_entity_destruction(self):
        entity = self.world.create_entity()
        self.world.add_component(entity, TestComponent())
        
        self.world.destroy_entity(entity)
        
        self.assertFalse(self.world.has_component(entity, TestComponent))
        self.assertEqual(len(self.world.get_entities_with(TestComponent)), 0)

if __name__ == '__main__':
    unittest.main()
