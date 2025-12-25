"""First-person camera controller for Panda3D."""

from panda3d.core import LVector3f
from typing import Optional, Any


class FPSCamera:
    """First-person camera controller using Panda3D."""
    
    def __init__(self, camera_node: Any, player_entity: Any, sensitivity: float = 40.0):
        """Initialize FPS Camera.
        
        Args:
            camera_node: Panda3D camera NodePath (base.camera)
            player_entity: The player entity/node to control
            sensitivity: Mouse sensitivity
        """
        self.camera = camera_node
        self.player = player_entity
        self.sensitivity = sensitivity
        self.clamp_vertical = True
        self.min_pitch = -89.0
        self.max_pitch = 89.0
        self.pitch = 0.0
        self.yaw = 0.0
        
    def update(self, mouse_dx: float, mouse_dy: float, dt: float) -> None:
        """Update camera rotation based on mouse movement.
        
        Args:
            mouse_dx: Mouse delta X (horizontal movement) - already per-frame
            mouse_dy: Mouse delta Y (vertical movement) - already per-frame
            dt: Delta time (not used for mouse input, which is already per-frame)
        """
        # Horizontal rotation (yaw)
        # NOTE: mouse_dx is already a per-frame delta, don't multiply by dt!
        self.yaw += mouse_dx * self.sensitivity
        
        # Vertical rotation (pitch)
        self.pitch -= mouse_dy * self.sensitivity
        
        # Clamp vertical rotation
        if self.clamp_vertical:
            self.pitch = max(self.min_pitch, min(self.max_pitch, self.pitch))
        
        # Apply rotations to camera
        # Panda3D uses HPR (Heading, Pitch, Roll)
        self.camera.setHpr(self.yaw, self.pitch, 0)
        
    def set_sensitivity(self, value: float) -> None:
        """Update mouse sensitivity."""
        self.sensitivity = value


class ThirdPersonCamera:
    """Third-person camera that orbits around a target entity."""
    
    def __init__(self, camera_node: Any, target_entity: Any, sensitivity: float = 40.0):
        """Initialize third-person camera.
        
        Args:
            camera_node: Panda3D camera NodePath (base.camera)
            target_entity: The entity/node to orbit around
            sensitivity: Mouse sensitivity for rotation
        """
        self.camera = camera_node
        self.target = target_entity
        self.sensitivity = sensitivity
        
        # Camera orbit parameters
        self.distance = 5.0  # Distance behind player
        self.height_offset = 2.0  # Height above player
        self.min_distance = 1.5  # Minimum distance (for collision)
        self.max_distance = 10.0
        
        # Rotation
        self.yaw = 0.0  # Horizontal rotation around player
        self.pitch = -15.0  # Vertical angle (looking down slightly)
        self.min_pitch = -60.0  # Don't look too far down
        self.max_pitch = 60.0  # Don't look too far up
        
        # Smoothing
        self.lerp_speed = 8.0  # How fast camera follows target
        self.current_distance = self.distance  # For collision smoothing
        
    def update(self, mouse_dx: float, mouse_dy: float, dt: float, target_position: LVector3f) -> None:
        """Update camera position and rotation.
        
        Args:
            mouse_dx: Mouse delta X (horizontal movement)
            mouse_dy: Mouse delta Y (vertical movement)
            dt: Delta time
            target_position: World position of the target entity
        """
        # Update rotation from mouse input
        # NOTE: mouse_dx/dy are already per-frame deltas, don't multiply by dt!
        self.yaw += mouse_dx * self.sensitivity
        self.pitch -= mouse_dy * self.sensitivity
        
        # Clamp pitch
        self.pitch = max(self.min_pitch, min(self.max_pitch, self.pitch))
        
        # Calculate desired camera position (orbit around target)
        import math
        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)
        
        # Offset from target
        offset_x = self.distance * math.sin(yaw_rad) * math.cos(pitch_rad)
        offset_y = -self.distance * math.cos(yaw_rad) * math.cos(pitch_rad)
        offset_z = self.distance * math.sin(pitch_rad) + self.height_offset
        
        desired_pos = target_position + LVector3f(offset_x, offset_y, offset_z)
        
        # Smooth camera movement (lerp)
        current_pos = self.camera.getPos()
        new_pos = current_pos + (desired_pos - current_pos) * (dt * self.lerp_speed)
        
        self.camera.setPos(new_pos)
        
        # Look at target (with height offset for better framing)
        look_at_target = target_position + LVector3f(0, 0, self.height_offset * 0.5)
        self.camera.lookAt(look_at_target)
    
    def set_sensitivity(self, value: float) -> None:
        """Update mouse sensitivity."""
        self.sensitivity = value
    
    def set_distance(self, distance: float) -> None:
        """Update orbit distance."""
        self.distance = max(self.min_distance, min(self.max_distance, distance))
