"""Camera state component for unified camera management."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional
from engine.ecs.component import Component, register_component


class CameraMode(Enum):
    """Camera perspective mode."""
    FIRST_PERSON = auto()
    EXPLORATION = auto()      # Third-person with auto-centering
    COMBAT = auto()           # Third-person with target framing
    CINEMATIC = auto()        # Future: scripted camera paths


@register_component
@dataclass
class CameraState(Component):
    """Unified camera state component.
    
    Consolidates all camera state (mode, rotation, zoom, animation)
    into a single ECS component for better state management.
    """
    
    # Mode
    mode: CameraMode = CameraMode.EXPLORATION
    toggle_cooldown: float = 0.0
    
    # Rotation (shared by all modes)
    yaw: float = 0.0
    pitch: float = 0.0
    
    # Third-person specific (EXPLORATION, COMBAT)
    distance: float = 5.0
    current_distance: float = 5.0  # For collision smoothing
    
    # Auto-centering (EXPLORATION, COMBAT)
    auto_center_strength: float = 0.3  # 0.0 = free orbit, 1.0 = always behind
    mouse_moved_recently: float = 0.0  # Timer for dead zone
    
    # Combat targeting (COMBAT mode)
    target_entity: Optional[int] = None  # Entity ID to frame in combat
    
    # Animation state
    bob_time: float = 0.0
    
    # Collision recovery (smoothing after forced zoom)
    collision_recovery_timer: float = 0.0
