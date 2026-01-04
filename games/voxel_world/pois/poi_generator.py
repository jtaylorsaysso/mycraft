"""
Points of Interest (POI) system for Voxel World.

This module handles the generation of discoverable locations like
shrines and enemy camps.
"""

from typing import Protocol, List, Tuple, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class POIData:
    """Metadata for a generated Point of Interest."""
    poi_type: str                  # Type identifier (e.g., "shrine_movement")
    position: Tuple[int, int, int] # Global world position (x, y, z) of the center/base
    blocks: List[Tuple[int, int, int, str]] # List of (x, y, z, block_name) relative to world
    entities: List[Tuple[str, int, int, int]] # List of (entity_type, x, y, z) for spawning
    loot: Dict[Tuple[int, int, int], List[str]] # Map of chest_pos -> list of item IDs
    rotation: int = 0              # Rotation in degrees (0, 90, 180, 270)

class POIGenerator:
    """Base class for Point of Interest generators."""
    
    def __init__(self, seed: int):
        self.seed = seed
        
    def should_spawn_at(self, chunk_x: int, chunk_z: int) -> bool:
        """Determine if this POI type should spawn in this chunk.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            
        Returns:
            True if POI should generate here
        """
        raise NotImplementedError
        
    def get_spawn_position(
        self, 
        chunk_x: int, 
        chunk_z: int, 
        chunk_size: int,
        biome_data: Any,
        height_callback: Any
    ) -> Optional[Tuple[int, int, int]]:
        """Find a suitable spawn position within the chunk.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            chunk_size: Size of chunk
            biome_data: Biome information for the chunk
            height_callback: Function to get terrain height at (x, z)
            
        Returns:
            (x, y, z) world coordinates or None if no valid spot found
        """
        raise NotImplementedError
        
    def generate(
        self, 
        x: int, 
        y: int, 
        z: int, 
        seed: int
    ) -> POIData:
        """Generate the POI structure and data.
        
        Args:
            x: World X coordinate of center/base
            y: World Y coordinate of base
            z: World Z coordinate of center/base
            seed: Distinct seed for this instance
            
        Returns:
            POIData containing blocks, entities, and metadata
        """
        raise NotImplementedError

    def flatten_terrain(
        self,
        center_x: int,
        center_z: int,
        base_y: int,
        radius: int,
        voxel_grid: Dict[Tuple[int, int, int], str],
        chunk_x: int,
        chunk_z: int,
        chunk_size: int
    ):
        """Helper to clear/flatten terrain for POI placement.
        
        Modifies voxel_grid in place.
        
        Args:
            center_x: World X of center
            center_z: World Z of center
            base_y: Target height
            radius: Radius to flatten
            voxel_grid: The chunk's voxel grid
            chunk_x: Current chunk X (for boundary checking)
            chunk_z: Current chunk Z
            chunk_size: Size of chunk
        """
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                wx = center_x + dx
                wz = center_z + dz
                
                # Check if in current chunk
                cx_check = wx // chunk_size
                cz_check = wz // chunk_size
                
                if cx_check == chunk_x and cz_check == chunk_z:
                    lx = wx % chunk_size
                    lz = wz % chunk_size
                    
                    # Fill below with dirt/stone up to base_y
                    # This is simple vertical filling, might need more complex logic for cliffs
                    voxel_grid[(lx, base_y, lz)] = "stone_bricks" # Foundation
                    
                    # Clear air above
                    for h in range(1, 15): # Clear generous headroom
                         if (lx, base_y + h, lz) in voxel_grid:
                             del voxel_grid[(lx, base_y + h, lz)]

