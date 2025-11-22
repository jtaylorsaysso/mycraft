from ursina import held_keys, mouse, Vec3, camera
from ursina import time
import math


class InputHandler:
    def __init__(self, player_entity):
        self.player = player_entity
        self.mouse_sensitivity = 20
        self.movement_speed = 5
        self.jump_height = 2
        self.gravity = -9.81
        self.velocity_y = 0
        self.grounded = True
        
        # Lock mouse for first-person control
        mouse.locked = True
        
    def input(self, key):
        """Handle key press events"""
        if key == 'space' and self.grounded:
            self.velocity_y = self.jump_height
            self.grounded = False
            
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
        
        # Apply gravity
        if not self.grounded:
            self.velocity_y += self.gravity * dt
            self.player.y += self.velocity_y * dt
            
            # Simple ground collision check (assuming ground at y=1)
            if self.player.y <= 2:  # Player feet at ground level
                self.player.y = 2
                self.velocity_y = 0
                self.grounded = True