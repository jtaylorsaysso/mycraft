"""
Enemy Component.

Tracks state for enemy entities including type, tint color, and AI state.
"""

from dataclasses import dataclass
from engine.ecs.component import Component, register_component

@register_component
@dataclass
class EnemyComponent(Component):
    """
    Component for enemy entities.
    """
    # Type of enemy (skeleton, zombie)
    enemy_type: str = "skeleton"
    
    # Visual tint color (name from ColorPalette)
    # This matches the color swatch they will drop
    tint_color: str = "white"
    
    # AI State
    ai_state: str = "idle"  # idle, aggro, windup, attack, recovery
    
    # Combat parameters
    aggro_range: float = 10.0
    attack_range: float = 2.0
    
    # State timers
    state_timer: float = 0.0
    
    # Target tracking
    target_id: str = ""
