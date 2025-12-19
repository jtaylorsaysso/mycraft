# MyCraft Engine - Physics Module

"""Physics subsystem for the MyCraft engine.

This module provides kinematic physics, collision detection, and
raycasting utilities for 3D games.

NOTE: Phase 1 - Temporary re-exports from old module structure.
This file currently re-exports from ../physics.py for backward compatibility.
In Phase 2, the actual implementations will be moved here.
"""

__version__ = "0.1.0"

# Temporary re-exports from old physics.py location
# This allows existing imports to continue working during migration
import sys
from pathlib import Path

# Import from parent directory's physics.py
parent_module = Path(__file__).parent.parent
sys.path.insert(0, str(parent_module))

try:
    # Re-export all public APIs from the old physics.py
    from engine import physics as _old_physics_module
    
    # Re-export main classes and functions
    KinematicState = _old_physics_module.KinematicState
    apply_gravity = _old_physics_module.apply_gravity
    integrate_movement = _old_physics_module.integrate_movement
    simple_flat_ground_check = _old_physics_module.simple_flat_ground_check
    perform_jump = _old_physics_module.perform_jump
    raycast_ground_height = _old_physics_module.raycast_ground_height
    raycast_wall_check = _old_physics_module.raycast_wall_check
    update_timers = _old_physics_module.update_timers
    register_jump_press = _old_physics_module.register_jump_press
    can_consume_jump = _old_physics_module.can_consume_jump
    
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
    ]
finally:
    # Clean up sys.path
    if str(parent_module) in sys.path:
        sys.path.remove(str(parent_module))

