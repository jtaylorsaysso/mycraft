# MyCraft Engine - Rendering Module

"""Rendering subsystem for the MyCraft engine.

This module provides rendering primitives including mesh generation,
texture atlas management, and camera systems.
"""

__version__ = "0.1.0"

from .texture_atlas import (
    TextureAtlas,
    TileRegistry
)

from .mesh import (
    MeshBuilder
)

from .base_camera import BaseCamera, CameraUpdateContext
from .first_person_camera import FirstPersonCamera
from .exploration_camera import ExplorationCamera
from .combat_camera import CombatCamera

# Trimesh utilities (optional - gracefully handles missing trimesh)
try:
    from .trimesh_utils import (
        is_available as trimesh_available,
        voxel_to_trimesh,
        simplify_collision_geometry,
        batch_ray_intersect,
        get_first_ray_hit,
        carve_sphere,
        carve_box,
        generate_smooth_mesh,
        get_surface_voxels,
        trimesh_to_geom_data
    )
except ImportError:
    trimesh_available = lambda: False

__all__ = [
    'TextureAtlas',
    'TileRegistry',
    'MeshBuilder',
    'BaseCamera',
    'CameraUpdateContext',
    'FirstPersonCamera',
    'ExplorationCamera',
    'CombatCamera',
    # Trimesh utilities
    'trimesh_available',
    'voxel_to_trimesh',
    'simplify_collision_geometry',
    'batch_ray_intersect',
    'get_first_ray_hit',
    'carve_sphere',
    'carve_box',
    'generate_smooth_mesh',
    'get_surface_voxels',
    'trimesh_to_geom_data'
]

