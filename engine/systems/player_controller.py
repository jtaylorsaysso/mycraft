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
        
        # Physics state
        self.physics_states = {}
        self.collision_traverser = CollisionTraverser('player_physics')
    
    def get_dependencies(self):
        return ["player"]
    
    def initialize(self):
        # Initialize input mechanic
        for mech in self.mechanics:
            if hasattr(mech, 'setup'):
                mech.setup(self.base)
    
    def on_ready(self):
        player_id = self.world.get_entity_by_tag("player")
        
        # Initialize camera mechanic
        for mech in self.mechanics:
            if hasattr(mech, 'initialize'):
                mech.initialize(player_id, self.world)
        
        super().on_ready()
    
    def update(self, dt):
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            return
        
        transform = self.world.get_component(player_id, Transform)
        if not transform:
            return
        
        # Ensure physics state
        if player_id not in self.physics_states:
            self.physics_states[player_id] = KinematicState()
        
        state = self.physics_states[player_id]
        
        # Build context
        ctx = PlayerContext(
            world=self.world,
            player_id=player_id,
            transform=transform,
            state=state,
            dt=dt
        )
        
        # Store base for ground_check access (hacky but works for MVP)
        ctx.world.base = self.base
        ctx.world.collision_traverser = self.collision_traverser
        
        # Run mechanics
        for mechanic in self.mechanics:
            if mechanic.can_handle(ctx):
                mechanic.update(ctx)
                if mechanic.exclusive:
                    break
        
        # Debug: Show execution order once
        if not hasattr(self, '_debug_shown'):
            self._debug_shown = True
            print(f"🔧 Mechanic execution order (priority):")
            for m in self.mechanics:
                print(f"   - {m.__class__.__name__}: priority={m.priority}")
        
        # Clear transition requests
        ctx.clear_requests()
