"""Player control coordinator using composition pattern."""

from engine.ecs.system import System
from engine.components.core import Transform
from engine.physics import KinematicState
from engine.player_mechanics.context import PlayerContext
from engine.player_mechanics.input_handler import InputMechanic
from engine.player_mechanics.camera_controller import CameraMechanic
from engine.player_mechanics.ground_movement import GroundMovementMechanic
from engine.player_mechanics.swimming import SwimmingMechanic
from engine.player_mechanics.animation import AnimationMechanic
from engine.player_mechanics.dodge_mechanic import DodgeMechanic
from engine.player_mechanics.parry_mechanic import ParryMechanic
from engine.player_mechanics.attack_mechanic import AttackMechanic
from engine.player_mechanics.targeting_mechanic import TargetingMechanic
from engine.player_mechanics.targeting_mechanic import TargetingMechanic
from panda3d.core import CollisionTraverser, LVector3f
from engine.components.avatar_colors import AvatarColors
from engine.components.projectile import ColorProjectileComponent

class PlayerControlSystem(System):
    """Coordinates player mechanics."""
    
    def __init__(self, world, event_bus, base):
        super().__init__(world, event_bus)
        self.base = base
        
        # Create mechanics
        self.mechanics = [
            InputMechanic(base),
            CameraMechanic(base),
            SwimmingMechanic(),  # Swimming controls (priority 40)
            GroundMovementMechanic(),  # Ground movement (priority 50, runs after swimming)
            DodgeMechanic(),  # Dodge input handling
            ParryMechanic(),  # Parry input handling
            AttackMechanic(),  # Attack input handling
            TargetingMechanic(), # Target locking
            AnimationMechanic(base),
        ]
        
        # Sort by priority
        self.mechanics.sort(key=lambda m: m.priority, reverse=True)
        
        # Collision system
        self.collision_traverser = CollisionTraverser('player_physics')
        
        # Reusable context (created in on_ready, updated each frame)
        self.player_context = None
        
        # Projectile State
        self.projectile_cooldown = 0.0
        self.projectile_max_cooldown = 3.0
    
    def get_dependencies(self):
        return ["player"]
    
    def initialize(self):
        for mech in self.mechanics:
            if hasattr(mech, 'setup'):
                mech.setup(self.base)
                
        # Register Projectile Input
        self.base.accept('r', self.throw_projectile)
    
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
        
        # Update cooldown
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= dt
        
        # Publish cooldown ratio for HUD (1.0 = ready, 0.0 = just fired)
        cooldown_ratio = 1.0 - (self.projectile_cooldown / self.projectile_max_cooldown) if self.projectile_max_cooldown > 0 else 1.0
        cooldown_ratio = max(0.0, min(1.0, cooldown_ratio))
        self.world._projectile_cooldown_ratio = cooldown_ratio
            
    def throw_projectile(self):
        """Throw a color projectile."""
        # Check cooldown
        if self.projectile_cooldown > 0:
            print("Projectile on cooldown")
            return
            
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            print("No player found")
            return
            
        # Get color
        colors = self.world.get_component(player_id, AvatarColors)
        if not colors:
            print("No AvatarColors found")
            return
            
        color_name = colors.current_color_name
        
        # Get spawn position (Head level + offset)
        transform = self.world.get_component(player_id, Transform)
        if not transform:
            print("No Transform found")
            return
            
        # Get camera orientation from CameraState component
        from engine.components.camera_state import CameraState
        import math
        
        camera_state = self.world.get_component(player_id, CameraState)
        if not camera_state:
            print("No CameraState found")
            return
        
        # Convert yaw/pitch to radians
        # Yaw: rotation around Z axis (heading)
        # Pitch: rotation around X axis (looking up/down)
        yaw_rad = math.radians(camera_state.yaw)
        pitch_rad = math.radians(camera_state.pitch)
        
        # Calculate forward vector in world space
        # In Panda3D: +Y is forward, +X is right, +Z is up
        # Yaw rotates around Z, Pitch rotates around local X
        forward = LVector3f(
            -math.sin(yaw_rad) * math.cos(pitch_rad),  # X component
            math.cos(yaw_rad) * math.cos(pitch_rad),   # Y component  
            math.sin(pitch_rad)                         # Z component
        )
        forward.normalize()
        
        spawn_pos = transform.position + LVector3f(0, 0, 1.6) + (forward * 1.0)
        
        velocity = forward * 25.0  # Increased speed for better range
        # Publish animation start event
        self.event_bus.publish("throw_projectile_start", entity_id=player_id)
        
        # Publish request event
        self.event_bus.publish("spawn_projectile", 
            position=spawn_pos, 
            velocity=velocity, 
            color_name=color_name, 
            owner_id=player_id
        )
        
        self.projectile_cooldown = self.projectile_max_cooldown
        print(f"Threw {color_name} projectile!")
