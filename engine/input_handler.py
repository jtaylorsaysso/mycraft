from ursina import held_keys, mouse, Vec3, camera
from ursina import time
import math

from engine.physics import (
    KinematicState,
    apply_gravity,
    integrate_movement,
    simple_flat_ground_check,
    perform_jump,
    update_timers,
    register_jump_press,
    can_consume_jump,
    raycast_ground_height,
    raycast_wall_check,
)


class InputHandler:
    def __init__(self, player_entity):
        self.player = player_entity
        self.player = player_entity
        self.mouse_sensitivity = 40
        self.movement_speed = 6
        self.acceleration = 40   # Units per second^2
        self.friction = 10       # Units per second^2 (on ground)
        self.air_control = 0.3   # Multiplier for air movement control
        
        # Mario-like baseline: higher jump, lighter gravity
        self.jump_height = 3.5
        self.gravity = -12.0 # Increased gravity for snappier fall
        self._physics_state = KinematicState(velocity_y=0.0, grounded=True)
        
        # Lock mouse for first-person control
        mouse.locked = True
        
    def input(self, key):
        """Handle key press events"""
        if key == 'space':
            # Record a jump request; actual jump will be performed in update()
            # based on coyote-time and buffering rules.
            register_jump_press(self._physics_state)
            
        # Toggle mouse lock with escape key
        if key == 'escape':
            mouse.locked = not mouse.locked
            
    def update(self, dt):
        """Update player movement and camera rotation every frame"""
        # Camera rotation with mouse
        if mouse.locked:
            # Horizontal rotation (yaw) - rotate player entity
            self.player.rotation_y += mouse.velocity[0] * self.mouse_sensitivity
            
            # Vertical rotation (pitch) - rotate camera pivot up/down
            if hasattr(self.player, 'camera_pivot'):
                self.player.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
                # Clamp vertical rotation to prevent over-rotation
                self.player.camera_pivot.rotation_x = max(-89, min(89, self.player.camera_pivot.rotation_x))
        
        # Movement input
        forward_input = held_keys['w'] - held_keys['s']
        strafe_input = held_keys['d'] - held_keys['a']
        
        # Calculate movement direction based on player rotation
        # Calculate target velocity based on inputs
        target_velocity = Vec3(0, 0, 0)
        
        if forward_input != 0 or strafe_input != 0:
            # Forward movement (relative to player rotation)
            forward = Vec3(
                math.sin(math.radians(self.player.rotation_y)),
                0,
                math.cos(math.radians(self.player.rotation_y))
            ) * forward_input
            
            # Strafe movement (perpendicular to forward)
            right = Vec3(
                math.cos(math.radians(self.player.rotation_y)),
                0,
                -math.sin(math.radians(self.player.rotation_y))
            ) * strafe_input
            
            # Combine movement vectors
            move_dir = (forward + right).normalized()
            target_velocity = move_dir * self.movement_speed

        # Apply acceleration/friction to approach target velocity
        # Different control in air vs ground
        control_factor = 1.0 if self._physics_state.grounded else self.air_control
        accel = self.acceleration * control_factor
        
        # Smoothly interpolate X velocity
        if target_velocity.x != 0:
            # Accelerating
            diff_x = target_velocity.x - self._physics_state.velocity_x
            change = accel * dt
            if abs(diff_x) < change:
                self._physics_state.velocity_x = target_velocity.x
            else:
                self._physics_state.velocity_x += math.copysign(change, diff_x)
        else:
            # Decelerating (Friction)
            fric = self.friction * dt * control_factor * 5 # Stronger stopping friction
            if abs(self._physics_state.velocity_x) < fric:
                self._physics_state.velocity_x = 0
            else:
                self._physics_state.velocity_x -= math.copysign(fric, self._physics_state.velocity_x)

        # Smoothly interpolate Z velocity
        if target_velocity.z != 0:
            # Accelerating
            diff_z = target_velocity.z - self._physics_state.velocity_z
            change = accel * dt
            if abs(diff_z) < change:
                self._physics_state.velocity_z = target_velocity.z
            else:
                self._physics_state.velocity_z += math.copysign(change, diff_z)
        else:
            # Decelerating (Friction)
            fric = self.friction * dt * control_factor * 5
            if abs(self._physics_state.velocity_z) < fric:
                self._physics_state.velocity_z = 0
            else:
                self._physics_state.velocity_z -= math.copysign(fric, self._physics_state.velocity_z)

        # Vertical physics: gravity and terrain-based ground using raycast
        apply_gravity(self._physics_state, dt, gravity=self.gravity, max_fall_speed=-30)

        def _ground_check(entity):
            # Use raycast to find the terrain height beneath the player.
            return raycast_ground_height(entity)

        def _wall_check(entity, movement):
             # Check if moving in this direction would hit something
             return raycast_wall_check(entity, movement, distance_buffer=0.5)

        integrate_movement(
            self.player,
            self._physics_state,
            dt,
            ground_check=_ground_check,
            wall_check=_wall_check
        )

        # Update coyote-time and jump-buffer timers now that grounded is up to date
        update_timers(self._physics_state, dt)

        # If we have a buffered jump and are within coyote time, perform the jump
        # Use generous Mario-like coyote and buffer windows
        if can_consume_jump(self._physics_state, coyote_time=0.2, jump_buffer_time=0.2):
            perform_jump(self._physics_state, self.jump_height)

        # Variable jump height: early release = short hop
        if self._physics_state.velocity_y > 0 and not held_keys['space']:
            self._physics_state.velocity_y *= 0.55