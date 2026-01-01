"""
Noise utilities for voxel_world terrain generation.

Re-exports from engine for backward compatibility.
"""

# Import directly from module to avoid panda3d dependency through __init__.py
from engine.world.noise import (
    get_noise,
    set_noise_seed,
    PerlinNoise2D,
)

__all__ = ['get_noise', 'set_noise_seed', 'PerlinNoise2D']


