"""
System base class for ECS logic.

Systems follow a three-phase lifecycle:
1. CONSTRUCTION: System object created, dependencies injected via __init__
2. INITIALIZATION: initialize() called to set up resources (no entity dependencies)
3. READY: on_ready() called when all declared dependencies are satisfied

Systems only receive update() calls when in READY state.
"""
from typing import TYPE_CHECKING, List
from engine.ecs.events import EventBus

if TYPE_CHECKING:
    from engine.ecs.world import World

class System:
    """
    Base class for logic systems.
    Systems operate on entities with specific components.
    
    Lifecycle:
        1. __init__: Construct system, store references
        2. initialize(): Setup resources that don't depend on entities
        3. on_ready(): Called when get_dependencies() are satisfied
        4. update(): Called every frame (only when ready=True)
        5. cleanup(): Teardown when system removed
    """
    def __init__(self, world: 'World', event_bus: EventBus):
        self.world = world
        self.event_bus = event_bus
        self.enabled = True
        self.ready = False  # System becomes ready when dependencies satisfied

    def get_dependencies(self) -> List[str]:
        """
        Declare entity tags this system requires before becoming ready.
        
        Returns:
            List of entity tag names (e.g., ["player", "camera"])
            Empty list means no dependencies (ready immediately)
            
        Example:
            def get_dependencies(self):
                return ["player"]  # Wait for player entity to exist
        """
        return []

    def initialize(self):
        """
        Phase 2: Setup resources that don't depend on entities.
        
        Called once when system is added to world.
        Do NOT access entities here - they may not exist yet.
        Use on_ready() for entity-dependent setup.
        """
        pass

    def on_ready(self):
        """
        Phase 3: Called when all dependencies from get_dependencies() are satisfied.
        
        This is where you should:
        - Access required entities
        - Setup entity-dependent resources
        - Lock input, create UI, etc.
        
        Default implementation sets ready=True.
        Override to add custom ready logic, but call super().on_ready()
        """
        self.ready = True

    def update(self, dt: float):
        """
        Called every frame when system is ready.
        
        Only called if:
        - self.enabled = True
        - self.ready = True
        
        Args:
            dt: Delta time since last frame in seconds
        """
        pass

    def cleanup(self):
        """
        Called when system is removed or game ends.
        
        Use this to:
        - Release resources
        - Unlock input
        - Remove event listeners
        - Clean up visual elements
        """
        pass
