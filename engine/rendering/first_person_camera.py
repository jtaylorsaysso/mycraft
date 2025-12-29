"""First-person camera controller."""

from typing import Any
from panda3d.core import LVector3f
from engine.rendering.base_camera import BaseCamera, CameraUpdateContext


class FirstPersonCamera(BaseCamera):
    """First-person camera with direct mouse control.
    
    Camera is positioned at player eye level and rotates directly
    with mouse input. No auto-centering or special behaviors.
    """
    
    def __init__(self, camera_node: Any, sensitivity: float = 40.0):
        """Initialize first-person camera.
        
        Args:
            camera_node: Panda3D camera NodePath (base.camera)
            sensitivity: Mouse sensitivity multiplier
        """
        self.camera = camera_node
        self.sensitivity = sensitivity
        self.clamp_vertical = True
        self.min_pitch = -89.0
        self.max_pitch = 89.0
        self.eye_height = 1.8  # Height above player position
    
    def update(self, ctx: CameraUpdateContext) -> None:
        """Update camera rotation and position.
        
        Args:
            ctx: Camera update context
        """
        # Update rotation from mouse input
        # NOTE: mouse_dx/dy are already per-frame deltas, don't multiply by dt!
        ctx.camera_state.yaw += ctx.mouse_delta[0] * self.sensitivity
        ctx.camera_state.pitch -= ctx.mouse_delta[1] * self.sensitivity
        
        # Clamp vertical rotation
        if self.clamp_vertical:
            ctx.camera_state.pitch = max(self.min_pitch, 
                                         min(self.max_pitch, ctx.camera_state.pitch))
        
        # Apply rotations to camera
        # Panda3D uses HPR (Heading, Pitch, Roll)
        self.camera.setHpr(ctx.camera_state.yaw, ctx.camera_state.pitch, 0)
        
        # Position camera at player eye level
        eye_position = ctx.target_position + LVector3f(0, 0, self.eye_height)
        self.camera.setPos(eye_position)
    
    def set_sensitivity(self, value: float) -> None:
        """Update mouse sensitivity.
        
        Args:
            value: New sensitivity value
        """
        self.sensitivity = value
