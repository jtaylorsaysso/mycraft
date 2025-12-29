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

__all__ = [
    'TextureAtlas',
    'TileRegistry',
    'MeshBuilder',
    'BaseCamera',
    'CameraUpdateContext',
    'FirstPersonCamera',
    'ExplorationCamera',
    'CombatCamera'
]
