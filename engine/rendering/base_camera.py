"""Base camera interface for all camera modes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from panda3d.core import LVector3f


@dataclass
class CameraUpdateContext:
    """Context object passed to camera update methods.
    
    Contains all necessary data for camera updates, avoiding
    parameter explosion in camera update signatures.
    """
    
    # Core references
    camera_node: Any              # Panda3D camera NodePath (base.cam)
    camera_state: Any             # CameraState ECS component
    target_position: LVector3f    # Player position
    player_velocity: LVector3f    # For camera bob and auto-centering
    
    # Input
    mouse_delta: tuple[float, float]  # Mouse movement this frame
    dt: float                          # Delta time
    
    # World reference (for querying targets)
    world: Any = None
    
    # Collision detection (optional)
    collision_traverser: Optional[Any] = None
    render_node: Optional[Any] = None


class BaseCamera(ABC):
    """Abstract base class for all camera modes.
    
    Defines the interface that all camera implementations must follow.
    Camera modes are stateless - all state is stored in CameraState component.
    """
    
    @abstractmethod
    def update(self, ctx: CameraUpdateContext) -> None:
        """Update camera position and orientation.
        
        Args:
            ctx: Camera update context with all necessary data
        """
        pass
    
    def on_enter(self, camera_state: Any) -> None:
        """Called when this camera mode becomes active.
        
        Override to perform initialization when switching to this mode.
        
        Args:
            camera_state: CameraState component
        """
        pass
    
    def on_exit(self, camera_state: Any) -> None:
        """Called when switching away from this camera mode.
        
        Override to perform cleanup when leaving this mode.
        
        Args:
            camera_state: CameraState component
        """
        pass
