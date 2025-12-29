"""
Core gameplay components.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple
from engine.ecs.component import Component, register_component
from panda3d.core import LVector3f as Vec3
from engine.physics.kinematic import KinematicState
from engine.components.camera_state import CameraState, CameraMode

@register_component
@dataclass
class Transform(Component):
    """Spatial representation."""
    position: Vec3 = field(default_factory=lambda: Vec3(0, 0, 0))
    rotation: Vec3 = field(default_factory=lambda: Vec3(0, 0, 0))
    scale: Vec3 = field(default_factory=lambda: Vec3(1, 1, 1))

@register_component
@dataclass
class Health(Component):
    """Health and damage tracking."""
    current: int = 100
    max_hp: int = 100
    invulnerable: bool = False
    invuln_timer: float = 0.0

@register_component
@dataclass
class Inventory(Component):
    """Item storage with stacking support.
    
    Each slot contains either None or a tuple of (item_type: str, count: int).
    """
    slots: List[Optional[Tuple[str, int]]] = field(default_factory=lambda: [None] * 9)
    selected_slot: int = 0
    max_stack: int = 64

@register_component
@dataclass
class Stamina(Component):
    """General resource for physical actions (combat & traversal).
    
    Used for:
    - Combat: Dodge, Parry
    - Traversal (future): Sprint, Climb, Swim, Vault
    """
    current: float = 100.0
    max_stamina: float = 100.0
    regen_rate: float = 20.0  # stamina per second
    regen_delay: float = 0.5  # delay after use before regen starts
    regen_timer: float = 0.0  # countdown to regen start

@register_component
@dataclass
class CombatState(Component):
    """Tracks player's combat state for animation and action constraints.
    
    Used for:
    - Preventing invalid actions (can't attack while dodging)
    - Animation state management
    - Visual feedback
    - Enemy AI (future)
    """
    state: str = "idle"  # idle, attacking, dodging, parrying, stunned
    state_timer: float = 0.0  # Time in current state
    
    # Action constraints (updated by combat systems)
    can_cancel: bool = True  # Can cancel into other actions
    can_attack: bool = True  # Can start new attack
    can_dodge: bool = True
    can_parry: bool = True
    
    # Dodge direction (set by input mechanic, used by dodge system)
    dodge_direction: Vec3 = field(default_factory=lambda: Vec3(0, 1, 0))  # Default forward

