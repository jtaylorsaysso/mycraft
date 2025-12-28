"""Camera state component for unified camera management."""

from enum import Enum, auto
from dataclasses import dataclass
from engine.ecs.component import Component, register_component


class CameraMode(Enum):
    """Camera perspective mode."""
    FIRST_PERSON = auto()
    THIRD_PERSON = auto()


@register_component
@dataclass
class CameraState(Component):
    """Unified camera state component.
    
    Consolidates all camera state (mode, rotation, zoom, animation)
    into a single ECS component for better state management.
    """
    
    # Mode
    mode: CameraMode = CameraMode.THIRD_PERSON
    toggle_cooldown: float = 0.0
    
    # Rotation (shared by both modes)
    yaw: float = 0.0
    pitch: float = 0.0
    
    # Third-person specific
    distance: float = 5.0
    current_distance: float = 5.0  # For collision smoothing
    
    # Animation state
    bob_time: float = 0.0
