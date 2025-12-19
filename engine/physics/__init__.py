# MyCraft Engine - Physics Module

"""Physics subsystem for the MyCraft engine.

This module provides kinematic physics, collision detection, and
raycasting utilities for 3D games.
"""

__version__ = "0.1.0"

from .kinematic import (
    KinematicState,
    apply_gravity,
    integrate_movement,
    simple_flat_ground_check,
    perform_jump,
    raycast_ground_height,
    raycast_wall_check,
    update_timers,
    register_jump_press,
    can_consume_jump,
    SupportsY
)

from .collision import (
    PlayerHitbox,
    get_hitbox
)

from .debug import (
    CollisionDebugRenderer
)

__all__ = [
    'KinematicState',
    'apply_gravity',
    'integrate_movement',
    'simple_flat_ground_check',
    'perform_jump',
    'raycast_ground_height',
    'raycast_wall_check',
    'update_timers',
    'register_jump_press',
    'can_consume_jump',
    'SupportsY',
    'PlayerHitbox',
    'get_hitbox',
    'CollisionDebugRenderer'
]
