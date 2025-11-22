from ursina import held_keys, mouse, Vec3, camera
from ursina import time
import math

from engine.physics import (
    KinematicState,
    apply_gravity,
    integrate_vertical,
    simple_flat_ground_check,
    perform_jump,
    update_timers,
    register_jump_press,
    can_consume_jump,
    raycast_ground_height,
)


class InputHandler:
    def __init__(self, player_entity):
        self.player = player_entity
        self.mouse_sensitivity = 20
        self.movement_speed = 5
        # Mario-like baseline: higher jump, lighter gravity
        self.jump_height = 3.5
        self.gravity = -8.0
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
            movement = (forward + right).normalized() * self.movement_speed * dt
            
            # Apply movement
            self.player.position += movement

        # Vertical physics: gravity and terrain-based ground using raycast
        apply_gravity(self._physics_state, dt, gravity=self.gravity, max_fall_speed=-20)

        def _ground_check(entity):
            # Use raycast to find the terrain height beneath the player.
            return raycast_ground_height(entity)

        integrate_vertical(
            self.player,
            self._physics_state,
            dt,
            ground_check=_ground_check,
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