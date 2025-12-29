"""
Simple Perlin-like noise implementation for terrain generation.

This module provides a lightweight 2D noise generator that produces
smooth, natural-looking random values suitable for terrain height maps.
"""

import math
from typing import Tuple


class PerlinNoise2D:
    """
    Simplified 2D Perlin-like noise generator.
    
    Uses a grid-based gradient noise approach similar to Perlin noise,
    but simplified for performance. Produces smooth, continuous random
    values that are ideal for terrain generation.
    """
    
    def __init__(self, seed: int = 0):
        """Initialize noise generator with a seed.
        
        Args:
            seed: Random seed for reproducible terrain
        """
        self.seed = seed
        # Permutation table for pseudo-random gradients
        self._perm = self._generate_permutation_table(seed)
    
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


def set_noise_seed(seed: int):
    """Change the global noise generator seed.
    
    Args:
        seed: New random seed
    """
    global _noise_generator
    _noise_generator = PerlinNoise2D(seed=seed)
