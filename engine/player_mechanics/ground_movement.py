"""Ground-based movement mechanic."""

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.physics import (
    apply_gravity, perform_jump, register_jump_press,
    can_consume_jump, apply_horizontal_acceleration,
    apply_slope_forces, integrate_movement
)
from engine.physics.constants import MOVE_SPEED, GRAVITY, JUMP_VELOCITY
from panda3d.core import LVector3f
import math


class PhysicsEntityWrapper:
    """Adapter to make Transform component compatible with physics functions.
    
    Physics functions expect an entity with x, y, z properties.
    This wrapper provides that interface for Transform components.
    """
    def __init__(self, transform):
        self.transform = transform
    
    @property
    def x(self): 
        return self.transform.position.x
    
    @x.setter
    def x(self, v): 
        self.transform.position.x = v
    
    @property
    def y(self): 
        return self.transform.position.y
    
    @y.setter
    def y(self, v): 
        self.transform.position.y = v
    
    @property
    def z(self): 
        return self.transform.position.z
    
    @z.setter
    def z(self, v): 
        self.transform.position.z = v


class GroundMovementMechanic(PlayerMechanic):
    """Handles standard ground movement, jumping, physics."""
    
    priority = 50  # Middle priority
    exclusive = False
    
    def can_handle(self, ctx: PlayerContext) -> bool:
        # Don't run if climbing/gliding/etc (checked via state flags)
        if hasattr(ctx.state, 'climbing') and ctx.state.climbing:
            return False
        return True
    
    def update(self, ctx: PlayerContext) -> None:
        # Calculate movement direction from input
        move_dir = LVector3f(0, 0, 0)
        h = ctx.world.base.cam.getH()  # Camera heading
        rad = math.radians(h)
        forward = LVector3f(-math.sin(rad), math.cos(rad), 0)
        right = LVector3f(math.cos(rad), math.sin(rad), 0)
        
        if ctx.input.forward: move_dir += forward
        if ctx.input.back: move_dir -= forward
        if ctx.input.left: move_dir -= right
        if ctx.input.right: move_dir += right
        
        if move_dir.length() > 0:
            move_dir.normalize()
        
        # Get settings from config
        speed = MOVE_SPEED
        g = GRAVITY
        jump_v = JUMP_VELOCITY
        god_mode = False
        fly_speed = 12.0
        
        if hasattr(ctx.world.base, 'config_manager') and ctx.world.base.config_manager:
            speed = ctx.world.base.config_manager.get("movement_speed", speed)
            g = ctx.world.base.config_manager.get("gravity", g)
            god_mode = ctx.world.base.config_manager.get("god_mode", False)
            fly_speed = ctx.world.base.config_manager.get("fly_speed", 12.0)
            h = ctx.world.base.config_manager.get("jump_height", None)
            if h is not None:
                jump_v = math.sqrt(2 * abs(g) * h)
        
        if god_mode:
            speed = fly_speed
            g = 0
            # Basic fly up/down
            if ctx.input.jump: move_dir.z += 1
            if ctx.input.crouch: move_dir.z -= 1

        # Apply horizontal acceleration (and vertical if in god_mode)
        target_vel = move_dir * speed
        
        if god_mode:
            # Direct velocity apply in god mode
            ctx.state.velocity = target_vel
        else:
            apply_horizontal_acceleration(
                ctx.state,
                (target_vel.x, target_vel.y),
                ctx.dt,
                ctx.state.grounded
            )
        
        # Vertical physics
        if not god_mode:
            if ctx.input.jump:
                register_jump_press(ctx.state)
            
            apply_gravity(ctx.state, ctx.dt, gravity=g)
            apply_slope_forces(ctx.state, ctx.dt)
            
            if can_consume_jump(ctx.state):
                perform_jump(ctx.state, jump_v)
            
        # Create wrapper for physics integration (reuses module-level class)
        entity_wrapper = PhysicsEntityWrapper(ctx.transform)
        
        # Ground and wall check functions for physics integration
        def ground_check(e):
            from engine.physics import raycast_ground_height
            return raycast_ground_height(e, ctx.world.collision_traverser, ctx.world.base.render)

        def wall_check(e, move):
            from engine.physics import raycast_wall_check
            return raycast_wall_check(
                e, 
                move, 
                ctx.world.collision_traverser, 
                ctx.world.base.render
            )
            
        if god_mode:
            # Direct position update (noclip)
            ctx.transform.position += ctx.state.velocity * ctx.dt
        else:
            integrate_movement(
                entity_wrapper, 
                ctx.state, 
                ctx.dt, 
                ground_check, 
                wall_check
            )
        
        # Update physics timers (coyote time, jump buffer)
        from engine.physics import update_timers
        update_timers(ctx.state, ctx.dt)
