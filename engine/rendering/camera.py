from ursina import mouse, Vec3, camera
from typing import Optional, Any

class FPSCamera:
    """First-person camera controller."""
    
    def __init__(self, player_entity: Any, sensitivity: float = 40.0):
        """Initialize FPS Camera.
        
        Args:
            player_entity: The entity to control (should have .rotation_y)
                           and optionally .camera_pivot (for rotation_x)
            sensitivity: Mouse sensitivity
        """
        self.player = player_entity
        self.sensitivity = sensitivity
        self.clamp_vertical = True
        self.min_pitch = -89.0
        self.max_pitch = 89.0
        
    def update(self, dt: float) -> None:
        """Update camera rotation based on mouse movement.
        
        Should be called every frame.
        """
        if mouse.locked:
            # Horizontal rotation (yaw) - rotate player entity
            self.player.rotation_y += mouse.velocity[0] * self.sensitivity
            
            # Vertical rotation (pitch) - rotate camera pivot up/down
            if hasattr(self.player, 'camera_pivot'):
                self.player.camera_pivot.rotation_x -= mouse.velocity[1] * self.sensitivity
                
                # Clamp vertical rotation to prevent over-rotation
                if self.clamp_vertical:
                    self.player.camera_pivot.rotation_x = max(
                        self.min_pitch, 
                        min(self.max_pitch, self.player.camera_pivot.rotation_x)
                    )
                    
    def set_sensitivity(self, value: float) -> None:
        """Update mouse sensitivity."""
        self.sensitivity = value
