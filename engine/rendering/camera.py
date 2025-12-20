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
            mouse_dx: Mouse delta X (horizontal movement)
            mouse_dy: Mouse delta Y (vertical movement)
            dt: Delta time
        """
        # Horizontal rotation (yaw)
        self.yaw += mouse_dx * self.sensitivity * dt
        
        # Vertical rotation (pitch)
        self.pitch -= mouse_dy * self.sensitivity * dt
        
        # Clamp vertical rotation
        if self.clamp_vertical:
            self.pitch = max(self.min_pitch, min(self.max_pitch, self.pitch))
        
        # Apply rotations to camera
        # Panda3D uses HPR (Heading, Pitch, Roll)
        self.camera.setHpr(self.yaw, self.pitch, 0)
        
    def set_sensitivity(self, value: float) -> None:
        """Update mouse sensitivity."""
        self.sensitivity = value
