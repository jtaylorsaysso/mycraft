"""
Engine-level world generation infrastructure.

Provides reusable chunk streaming, noise generation, and collision utilities
that games can leverage without reimplementing.
"""

# Noise utilities - no heavy dependencies
from engine.world.noise import get_noise, set_noise_seed, PerlinNoise2D
from engine.world.generator import ChunkGenerator

# ChunkManager requires panda3d - import on demand
def get_chunk_manager():
    """Get ChunkManager class (lazy import to avoid panda3d dependency at package level)."""
    from engine.world.chunk_manager import ChunkManager
    return ChunkManager

__all__ = [
    'get_noise',
    'set_noise_seed', 
    'PerlinNoise2D',
    'ChunkGenerator',
    'get_chunk_manager',
]

