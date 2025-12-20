"""
Advanced gameplay components.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from engine.ecs.component import Component, register_component
from ursina import Vec3

@register_component
@dataclass
class Trigger(Component):
    """Zone detection."""
    bounds_min: Vec3 = field(default_factory=lambda: Vec3(0, 0, 0))
    bounds_max: Vec3 = field(default_factory=lambda: Vec3(1, 1, 1))
    one_shot: bool = False
    triggered: bool = False
    on_enter_event: Optional[str] = None
    on_exit_event: Optional[str] = None

@register_component
@dataclass
class Pathfinder(Component):
    """AI movement."""
    target_position: Optional[Vec3] = None
    target_entity: Optional[str] = None
    speed: float = 1.0
    arrival_distance: float = 1.0
    path: List[Vec3] = field(default_factory=list)

@register_component
@dataclass
class Timer(Component):
    """Scheduled events."""
    duration: float = 1.0
    elapsed: float = 0.0
    loop: bool = False
    active: bool = True
    on_complete_event: str = "timer_complete"

@register_component
@dataclass
class Score(Component):
    """Points tracking."""
    value: int = 0
    display_name: str = "Score"

@register_component
@dataclass
class Spawner(Component):
    """Entity spawning."""
    entity_prefab: str = ""
    interval: float = 5.0
    timer: float = 0.0
    max_active: int = 10
    spawned_ids: List[str] = field(default_factory=list)
