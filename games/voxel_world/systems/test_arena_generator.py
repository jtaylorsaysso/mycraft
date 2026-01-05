"""Test Arena Generator for mechanics verification.

Generates a small 5x5 chunk arena with guaranteed content placement.
"""

from typing import Dict, Tuple, Any, List, Optional

from games.voxel_world.blocks.blocks import BlockRegistry
from games.voxel_world.pois import POIData
from games.voxel_world.pois.camp_generator import CampGenerator
from games.voxel_world.pois.shrine_generator import ShrineGenerator

class TestArenaGenerator:
    """Small test arena generator with deterministic layout."""
    
    def __init__(self, seed: int = 0):
        self.world_seed = seed
        self.arena_radius = 2 # 5x5 chunks (-2 to 2)
        
    def generate_chunk(
        self, 
        chunk_x: int, 
        chunk_z: int,
        chunk_size: int
    ) -> Tuple[Dict[Tuple[int, int, int], str], List[Tuple[str, int, int, int]]]:
        """Generate test arena chunk."""
        
        # 1. Check bounds - only generate 5x5 area
        if abs(chunk_x) > self.arena_radius or abs(chunk_z) > self.arena_radius:
            return {}, []
            
        voxel_grid = {}
        entities = []
        
        # 2. Create flat terrain
        # Base height y=5
        for x in range(chunk_size):
            for z in range(chunk_size):
                # Surface (Grass)
                voxel_grid[(x, 5, z)] = "grass"
                # Dirt layer
                voxel_grid[(x, 4, z)] = "dirt"
                voxel_grid[(x, 3, z)] = "dirt"
                # Stone base
                for y in range(2, -1, -1):
                    voxel_grid[(x, y, z)] = "stone"
                    
                # Add some visual variety (stone patches)
                if (x + z + chunk_x + chunk_z) % 7 == 0:
                    voxel_grid[(x, 5, z)] = "stone"

        # 3. Add Content based on chunk coordinates
        # Center (0,0): Spawn area (handled by game logic, but we can verify ground is clear)
        
        # Northeast (1, 1): Enemy Camp
        if chunk_x == 1 and chunk_z == 1:
            self._place_poi(CampGenerator(self.world_seed), chunk_x, chunk_z, chunk_size, voxel_grid, entities)
            
        # Southwest (-1, -1): Enemy Camp
        elif chunk_x == -1 and chunk_z == -1:
            self._place_poi(CampGenerator(self.world_seed + 1), chunk_x, chunk_z, chunk_size, voxel_grid, entities)
            
        # Northwest (-1, 1): Shrine
        elif chunk_x == -1 and chunk_z == 1:
            self._place_poi(ShrineGenerator(self.world_seed), chunk_x, chunk_z, chunk_size, voxel_grid, entities)
            
        # Southeast (1, -1): Shrine
        elif chunk_x == 1 and chunk_z == -1:
            self._place_poi(ShrineGenerator(self.world_seed + 1), chunk_x, chunk_z, chunk_size, voxel_grid, entities)
            
        return voxel_grid, entities

    def _place_poi(self, generator, chunk_x, chunk_z, chunk_size, voxel_grid, entities_out):
        """Helper to place a POI in the center of the chunk."""
        center_x = chunk_x * chunk_size + (chunk_size // 2)
        center_z = chunk_z * chunk_size + (chunk_size // 2)
        base_y = 5
        
        # Flatten (ensure air above)
        generator.flatten_terrain(center_x, center_z, base_y, 4, voxel_grid, chunk_x, chunk_z, chunk_size)
        
        # Generate
        poi_data = generator.generate(center_x, base_y, center_z, self.world_seed)
        
        # Add blocks
        for bx, by, bz, bname in poi_data.blocks:
            rx = bx - (chunk_x * chunk_size)
            rz = bz - (chunk_z * chunk_size)
            
            if 0 <= rx < chunk_size and 0 <= rz < chunk_size:
                voxel_grid[(rx, by, rz)] = bname
                
        # Add entities
        entities_out.extend(poi_data.entities)

    def get_height(self, x: float, z: float) -> float:
        """Constant height for test arena."""
        return 5.0

    def get_block_registry(self) -> Any:
        return BlockRegistry

def create_test_arena_system(world, event_bus, base, texture_atlas=None, seed=0):
    """Factory for test arena system."""
    from engine.world.chunk_manager import ChunkManager
    
    generator = TestArenaGenerator(seed=seed)
    
    # Get config if available (reuse existing logic)
    complex_water = False
    if hasattr(base, 'config_manager'):
        complex_water = base.config_manager.get('complex_water', False)
    
    return ChunkManager(
        world=world,
        event_bus=event_bus,
        base=base,
        generator=generator,
        texture_atlas=texture_atlas,
        chunk_size=16,
        load_radius=6,
        unload_radius=8,
        max_chunks_per_frame=10, # Load faster for small arena
        sea_level=0, 
        complex_water=complex_water
    )
