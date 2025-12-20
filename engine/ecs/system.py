"""
System base class for ECS logic.
"""
from typing import TYPE_CHECKING, List, Type
from engine.ecs.events import EventBus

if TYPE_CHECKING:
    from engine.ecs.world import World

class System:
    """
    Base class for logic systems.
    Systems operate on entities with specific components.
    """
    def __init__(self, world: 'World', event_bus: EventBus):
        self.world = world
        self.event_bus = event_bus
        self.enabled = True

    def initialize(self):
        """Called once when system is added to world."""
        pass

    def update(self, dt: float):
        """Called every frame."""
        pass

    def cleanup(self):
        """Called when system is removed or game ends."""
        pass
