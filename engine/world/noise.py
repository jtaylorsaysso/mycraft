"""
Procedural noise utilities for terrain generation.

This module provides Perlin-like noise generators suitable for
terrain height maps, biome selection, and other procedural content.

Includes both scalar (per-point) and vectorized (NumPy) implementations
for flexibility and performance optimization.
"""

import math
from typing import Tuple, Optional
import numpy as np
from numpy.typing import NDArray


class PerlinNoise2D:
    """
    Simplified 2D Perlin-like noise generator.
    
    Uses a grid-based gradient noise approach similar to Perlin noise,
    but simplified for performance. Produces smooth, continuous random
    values that are ideal for terrain generation.
    
    Supports both scalar (single-point) and vectorized (batch) operations.
    """
    
    def __init__(self, seed: int = 0):
        """Initialize noise generator with a seed.
        
        Args:
            seed: Random seed for reproducible terrain
        """
        self.seed = seed
        # Permutation table for pseudo-random gradients
        self._perm = self._generate_permutation_table(seed)
        # NumPy version of permutation table for vectorized ops
        self._perm_np = np.array(self._perm, dtype=np.int32)
    
    def _generate_permutation_table(self, seed: int) -> list:
        """Generate a permutation table for gradient lookups."""
        import random
        rng = random.Random(seed)
        p = list(range(256))
        rng.shuffle(p)
        # Duplicate to avoid modulo operations
        return p + p
    
    def _fade(self, t: float) -> float:
        """Smooth interpolation curve (6t^5 - 15t^4 + 10t^3)."""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linear interpolation."""
        return a + t * (b - a)
    
    def _grad(self, hash_val: int, x: float, y: float) -> float:
        """Calculate dot product of gradient vector and distance vector."""
        # Use hash to select gradient direction
        h = hash_val & 3
        if h == 0:
            return x + y
        elif h == 1:
            return -x + y
        elif h == 2:
            return x - y
        else:
            return -x - y
    
    def noise(self, x: float, y: float) -> float:
        """Generate 2D Perlin noise value at coordinates (x, y).
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Noise value in range approximately [-1, 1]
        """
        # Find unit grid cell containing point
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        
        # Relative position within cell
        x -= math.floor(x)
        y -= math.floor(y)
        
        # Compute fade curves
        u = self._fade(x)
        v = self._fade(y)
        
        # Hash coordinates of 4 grid corners
        aa = self._perm[self._perm[X] + Y]
        ab = self._perm[self._perm[X] + Y + 1]
        ba = self._perm[self._perm[X + 1] + Y]
        bb = self._perm[self._perm[X + 1] + Y + 1]
        
        # Blend results from 4 corners
        return self._lerp(
            self._lerp(self._grad(aa, x, y), self._grad(ba, x - 1, y), u),
            self._lerp(self._grad(ab, x, y - 1), self._grad(bb, x - 1, y - 1), u),
            v
        )
    
    def octave_noise(self, x: float, y: float, octaves: int = 4, 
                     persistence: float = 0.5, lacunarity: float = 2.0) -> float:
        """Generate fractal noise by combining multiple octaves.
        
        Args:
            x: X coordinate
            y: Y coordinate
            octaves: Number of noise layers to combine
            persistence: Amplitude multiplier for each octave (0-1)
            lacunarity: Frequency multiplier for each octave (typically 2.0)
            
        Returns:
            Combined noise value
        """
        total = 0.0
        frequency = 1.0
        amplitude = 1.0
        max_value = 0.0  # For normalization
        
        for _ in range(octaves):
            total += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        
        # Normalize to approximately [-1, 1]
        return total / max_value

    # =========================================================================
    # Vectorized (NumPy) methods for batch processing
    # =========================================================================
    
    def _fade_np(self, t: NDArray[np.float32]) -> NDArray[np.float32]:
        """Vectorized fade function."""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _grad_np(self, hash_arr: NDArray[np.int32], x: NDArray[np.float32], 
                 y: NDArray[np.float32]) -> NDArray[np.float32]:
        """Vectorized gradient calculation."""
        h = hash_arr & 3
        result = np.empty_like(x)
        
        mask0 = h == 0
        mask1 = h == 1
        mask2 = h == 2
        mask3 = h == 3
        
        result[mask0] = x[mask0] + y[mask0]
        result[mask1] = -x[mask1] + y[mask1]
        result[mask2] = x[mask2] - y[mask2]
        result[mask3] = -x[mask3] - y[mask3]
        
        return result
    
    def noise_batch(self, xs: NDArray[np.float32], ys: NDArray[np.float32]) -> NDArray[np.float32]:
        """Generate noise for arrays of coordinates.
        
        Args:
            xs: X coordinates array
            ys: Y coordinates array
            
        Returns:
            Noise values array
        """
        # Grid cell coordinates
        X = np.floor(xs).astype(np.int32) & 255
        Y = np.floor(ys).astype(np.int32) & 255
        
        # Relative positions within cells
        x = xs - np.floor(xs)
        y = ys - np.floor(ys)
        
        # Fade curves
        u = self._fade_np(x)
        v = self._fade_np(y)
        
        # Hash lookups (vectorized)
        aa = self._perm_np[self._perm_np[X] + Y]
        ab = self._perm_np[self._perm_np[X] + Y + 1]
        ba = self._perm_np[self._perm_np[X + 1] + Y]
        bb = self._perm_np[self._perm_np[X + 1] + Y + 1]
        
        # Gradient contributions
        g_aa = self._grad_np(aa, x, y)
        g_ba = self._grad_np(ba, x - 1, y)
        g_ab = self._grad_np(ab, x, y - 1)
        g_bb = self._grad_np(bb, x - 1, y - 1)
        
        # Bilinear interpolation
        lerp_x0 = g_aa + u * (g_ba - g_aa)
        lerp_x1 = g_ab + u * (g_bb - g_ab)
        
        return lerp_x0 + v * (lerp_x1 - lerp_x0)
    
    def noise_grid(self, x_start: float, z_start: float, width: int, depth: int,
                   scale: float = 1.0) -> NDArray[np.float32]:
        """Generate a 2D grid of noise values.
        
        Optimized for generating entire chunk heightmaps at once.
        
        Args:
            x_start: World X coordinate of grid origin
            z_start: World Z coordinate of grid origin
            width: Grid width (X axis)
            depth: Grid depth (Z axis)
            scale: Coordinate scale factor
            
        Returns:
            2D array of noise values (width, depth)
        """
        # Create coordinate grids
        x_coords = (np.arange(width) + x_start) * scale
        z_coords = (np.arange(depth) + z_start) * scale
        xs, zs = np.meshgrid(x_coords, z_coords, indexing='ij')
        
        return self.noise_batch(xs.flatten(), zs.flatten()).reshape(width, depth)
    
    def octave_noise_grid(self, x_start: float, z_start: float, width: int, depth: int,
                          scale: float = 1.0, octaves: int = 4,
                          persistence: float = 0.5, lacunarity: float = 2.0) -> NDArray[np.float32]:
        """Generate fractal noise for entire grid at once.
        
        Args:
            x_start: World X coordinate of grid origin
            z_start: World Z coordinate of grid origin
            width: Grid width
            depth: Grid depth
            scale: Base coordinate scale
            octaves: Number of noise layers
            persistence: Amplitude multiplier per octave
            lacunarity: Frequency multiplier per octave
            
        Returns:
            2D array of noise values (width, depth)
        """
        total = np.zeros((width, depth), dtype=np.float32)
        frequency = 1.0
        amplitude = 1.0
        max_value = 0.0
        
        for _ in range(octaves):
            total += self.noise_grid(x_start, z_start, width, depth, 
                                     scale * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        
        return total / max_value


# Global noise generator instance (can be re-seeded)
_noise_generator = PerlinNoise2D(seed=12345)


def get_noise(x: float, y: float, scale: float = 1.0, octaves: int = 4) -> float:
    """Convenience function to get noise value.
    
    Args:
        x: X coordinate
        y: Y coordinate  
        scale: Scale factor for coordinates (smaller = larger features)
        octaves: Number of noise layers
        
    Returns:
        Noise value in range approximately [-1, 1]
    """
    return _noise_generator.octave_noise(x * scale, y * scale, octaves=octaves)


def get_noise_grid(x_start: float, z_start: float, width: int, depth: int,
                   scale: float = 1.0, octaves: int = 4) -> NDArray[np.float32]:
    """Get a grid of noise values (vectorized, faster for chunks).
    
    Args:
        x_start: World X coordinate of grid origin
        z_start: World Z coordinate of grid origin
        width: Grid width
        depth: Grid depth
        scale: Coordinate scale factor
        octaves: Number of noise layers
        
    Returns:
        2D array of noise values (width, depth)
    """
    return _noise_generator.octave_noise_grid(x_start, z_start, width, depth, scale, octaves)


def set_noise_seed(seed: int):
    """Change the global noise generator seed.
    
    Args:
        seed: New random seed
    """
    global _noise_generator
    _noise_generator = PerlinNoise2D(seed=seed)

