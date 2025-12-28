"""Player control coordinator using composition pattern."""

from engine.ecs.system import System
from engine.components.core import Transform
from engine.physics import KinematicState
from engine.player_mechanics.context import PlayerContext
from engine.player_mechanics.input_handler import InputMechanic
from engine.player_mechanics.camera_controller import CameraMechanic
from engine.player_mechanics.ground_movement import GroundMovementMechanic
from engine.player_mechanics.animation import AnimationMechanic
from panda3d.core import CollisionTraverser

class PlayerControlSystem(System):
    """Coordinates player mechanics."""
    
    def __init__(self, world, event_bus, base):
        super().__init__(world, event_bus)
        self.base = base
        
        # Create mechanics
        self.mechanics = [
            InputMechanic(base),
            CameraMechanic(base),
            GroundMovementMechanic(),
            AnimationMechanic(base),
        ]
        
        # Sort by priority
        self.mechanics.sort(key=lambda m: m.priority, reverse=True)
        
        # Collision system
        self.collision_traverser = CollisionTraverser('player_physics')
        
        # Reusable context (created in on_ready, updated each frame)
        self.player_context = None
    
    def get_dependencies(self):
        return ["player"]
    
    def initialize(self):
        # Initialize input mechanic
        for mech in self.mechanics:
            if hasattr(mech, 'setup'):
                mech.setup(self.base)
    
    def on_ready(self):
        player_id = self.world.get_entity_by_tag("player")
        
        # Share collision system with the world so mechanics can find it
        self.world.collision_traverser = self.collision_traverser
        
        # Initialize mechanics
        for mech in self.mechanics:
            if hasattr(mech, 'initialize'):
                mech.initialize(player_id, self.world)
        
        # Create reusable PlayerContext once
        transform = self.world.get_component(player_id, Transform)
        state = self.world.get_component(player_id, KinematicState)
        
        if transform and state:
            self.player_context = PlayerContext(
                world=self.world,
                player_id=player_id,
                transform=transform,
                state=state,
                dt=0.0
            )
            # Store base for ground_check access (hacky but works for MVP)
            self.player_context.world.base = self.base
            self.player_context.world.collision_traverser = self.collision_traverser
        
        super().on_ready()
    
    def update(self, dt):
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            return
        
        transform = self.world.get_component(player_id, Transform)
        state = self.world.get_component(player_id, KinematicState)
        
        if not transform or not state:
            return
        
        # Update context in-place (no allocation)
        if self.player_context is None:
            # Fallback: create context if not initialized (shouldn't happen)
            self.player_context = PlayerContext(
                world=self.world,
                player_id=player_id,
                transform=transform,
                state=state,
                dt=dt
            )
            self.player_context.world.base = self.base
            self.player_context.world.collision_traverser = self.collision_traverser
        else:
            # Normal path: update existing context
            self.player_context.update_refs(transform, state, dt)
        
        # Run mechanics
        for mechanic in self.mechanics:
            if mechanic.can_handle(self.player_context):
                mechanic.update(self.player_context)
                if mechanic.exclusive:
                    break
        
        # Debug: Show execution order once
        if not hasattr(self, '_debug_shown'):
            self._debug_shown = True
            print(f"🔧 Mechanic execution order (priority):")
            for m in self.mechanics:
                print(f"   - {m.__class__.__name__}: priority={m.priority}")
        
        # Clear transition requests
        self.player_context.clear_requests()
