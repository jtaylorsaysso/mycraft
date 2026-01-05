"""
Color Projectile Component.

Tracks state for thrown color projectiles.
"""

from dataclasses import dataclass
from engine.ecs.component import Component, register_component
from panda3d.core import LVector3f

@register_component
@dataclass
class ColorProjectileComponent(Component):
    """Component for a color projectile."""
    color_name: str = "white"
    owner_id: str = ""       # Entity ID of shooter (to avoid self-collision)
    velocity: LVector3f = LVector3f(0, 0, 0)
    gravity: float = 5.0     # Reduced gravity for better range
    lifetime: float = 5.0    # Seconds before despawn (increased for longer range)
    radius: float = 0.5      # Collision radius
    damage: float = 0.0      # Currently 0 damage, just cosmetic
