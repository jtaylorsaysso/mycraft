"""Base structure generator for procedural world decoration.

This module provides the core framework for generating structures (trees, boulders,
etc.) during chunk generation. Individual structure types inherit from StructureGenerator
and implement their own placement logic.
"""

from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
from games.voxel_world.biomes.noise import get_noise
import random


@dataclass
class Structure:
    """Represents a structure to be placed in the world.
    
    Attributes:
        blocks: List of (x, y, z, block_name) tuples defining the structure
        origin: (x, y, z) world coordinates of the structure's base
    """
    blocks: List[Tuple[int, int, int, str]]
    origin: Tuple[int, int, int]


class StructureGenerator:
    """Base class for procedural structure generation.
    
    The structure generation workflow:
    1. Chunk generation calculates heightmap
    2. For each biome, check if structures should spawn
    3. Use noise/random to determine spawn positions
    4. Generate structure at each position
    5. Add structure blocks to chunk data (before meshing)
    
    Design principles:
    - Structures are generated per-chunk for consistent world gen
    - Noise-based placement ensures deterministic results (same seed = same world)
    - Structures can span chunk boundaries (handled by querying neighbors)
    - Placement validation prevents floating trees, underground boulders, etc.
    """
    
    def __init__(self, seed: int = 0):
        """Initialize structure generator.
        
        Args:
            seed: World seed for deterministic generation
        """
        self.seed = seed
        self.random = random.Random(seed)
    
    def should_generate_at(
        self, 
        x: int, 
        z: int, 
        density: float = 0.05,
        scale: float = 0.2
    ) -> bool:
        """Determine if a structure should generate at world coordinates.
        
        Uses Perlin noise to create natural clustering and distribution.
        
        Args:
            x: World X coordinate
            z: World Z coordinate
            density: Probability threshold (0.0-1.0). Higher = more structures
            scale: Noise scale. Lower = larger clusters, higher = more scattered
            
        Returns:
            True if structure should generate at this position
        """
        # Use noise for natural distribution
        noise_value = get_noise(
            x + self.seed, 
            z + self.seed, 
            scale=scale, 
            octaves=2
        )
        
        # Normalize noise to [0, 1] range
        normalized = (noise_value + 1.0) / 2.0
        
        return normalized > (1.0 - density)
    
    def get_spawn_positions(
        self,
        chunk_x: int,
        chunk_z: int,
        chunk_size: int,
        density: float = 0.05,
        scale: float = 0.2,
        spacing: int = 3
    ) -> List[Tuple[int, int]]:
        """Get all valid spawn positions within a chunk.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            chunk_size: Size of chunk in blocks
            density: Structure density (0.0-1.0)
            scale: Noise scale for distribution
            spacing: Minimum blocks between structures
            
        Returns:
            List of (x, z) world coordinates for structure spawns
        """
        positions = []
        base_x = chunk_x * chunk_size
        base_z = chunk_z * chunk_size
        
        # Check every Nth block to avoid overcrowding
        for x in range(0, chunk_size, spacing):
            for z in range(0, chunk_size, spacing):
                world_x = base_x + x
                world_z = base_z + z
                
                if self.should_generate_at(world_x, world_z, density, scale):
                    positions.append((world_x, world_z))
        
        return positions
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        """Generate a structure at given position.
        
        Override this method in subclasses to implement specific structure types.
        
        Args:
            x: World X coordinate (base/center)
            y: World Y coordinate (ground level)
            z: World Z coordinate (base/center)
            height_callback: Function to query terrain height at any (x, z)
            
        Returns:
            Structure instance or None if placement invalid
        """
        raise NotImplementedError("Subclasses must implement generate_structure()")
    
    def validate_placement(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int],
        min_flat_radius: int = 1
    ) -> bool:
        """Validate that terrain is suitable for structure placement.
        
        Checks for relatively flat ground to prevent floating trees
        or structures buried in hillsides.
        
        Args:
            x: World X coordinate
            y: Proposed base Y coordinate
            z: World Z coordinate
            height_callback: Function to query terrain height
            min_flat_radius: Radius in blocks to check for flatness
            
        Returns:
            True if placement is valid
        """
        # Check terrain height in a radius around position
        for dx in range(-min_flat_radius, min_flat_radius + 1):
            for dz in range(-min_flat_radius, min_flat_radius + 1):
                terrain_height = height_callback(x + dx, z + dz)
                
                # Allow ±1 block variation for gentle slopes
                if abs(terrain_height - y) > 1:
                    return False
        
        return True
