"""
Core gameplay components.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Any
from engine.ecs.component import Component, register_component
from ursina import Vec3

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
    """Item storage."""
    slots: List[Optional[str]] = field(default_factory=lambda: [None] * 9)
    selected_slot: int = 0
    max_stack: int = 64
