"""Enhanced Test Arena Generator for comprehensive feature verification.

Generates a 7x7 chunk arena with distinct testing zones:
- Central Spawn Hub (0,0)
- Combat Arena (NE)
- Movement Course (SE)
- Water Pool (SW)
- POI Zone (NW)
- Projectile Range (N)
"""

from typing import Dict, Tuple, Any, List, Optional
import math

from games.voxel_world.blocks.blocks import BlockRegistry
from games.voxel_world.pois import POIData
from games.voxel_world.pois.camp_generator import CampGenerator
from games.voxel_world.pois.shrine_generator import ShrineGenerator

class TestArenaGenerator:
    """Enhanced test arena generator with distinct testing zones."""
    
    def __init__(self, seed: int = 0):
        self.world_seed = seed
        self.arena_radius = 3  # 7x7 chunks (-3 to 3)
        self.base_height = 5
        
    def generate_chunk(
        self, 
        chunk_x: int, 
        chunk_z: int,
        chunk_size: int
    ) -> Tuple[Dict[Tuple[int, int, int], str], List[Tuple[str, int, int, int]], Dict[Tuple[int, int, int], List[str]]]:
        """Generate test arena chunk with zone-specific features."""
        
        # 1. Check bounds - only generate 7x7 area
        if abs(chunk_x) > self.arena_radius or abs(chunk_z) > self.arena_radius:
            return {}, [], {}
            
        voxel_grid = {}
        entities = []
        chest_loot = {}  # Dictionary of (x, y, z) -> list of item names
        
        # 2. Determine zone and generate accordingly
        zone = self._get_zone(chunk_x, chunk_z)
        
        if zone == "spawn_hub":
            self._generate_spawn_hub(chunk_x, chunk_z, chunk_size, voxel_grid, entities)
        elif zone == "combat_arena":
            self._generate_combat_arena(chunk_x, chunk_z, chunk_size, voxel_grid, entities)
        elif zone == "movement_course":
            self._generate_movement_course(chunk_x, chunk_z, chunk_size, voxel_grid, entities)
        elif zone == "water_pool":
            self._generate_water_pool(chunk_x, chunk_z, chunk_size, voxel_grid, entities)
        elif zone == "poi_zone":
            self._generate_poi_zone(chunk_x, chunk_z, chunk_size, voxel_grid, entities, chest_loot)
        elif zone == "projectile_range":
            self._generate_projectile_range(chunk_x, chunk_z, chunk_size, voxel_grid, entities)
        else:
            # Default flat terrain for edge chunks
            self._generate_flat_terrain(chunk_x, chunk_z, chunk_size, voxel_grid)
            
        return voxel_grid, entities, chest_loot
    
    def _get_zone(self, chunk_x: int, chunk_z: int) -> str:
        """Determine which testing zone this chunk belongs to."""
        # Central spawn hub
        if chunk_x == 0 and chunk_z == 0:
            return "spawn_hub"
        
        # Combat Arena: NE quadrant (chunks 1-2, 1-2)
        if chunk_x in [1, 2] and chunk_z in [1, 2]:
            return "combat_arena"
        
        # Movement Course: SE quadrant (chunks 1-2, -1 to -2)
        if chunk_x in [1, 2] and chunk_z in [-1, -2]:
            return "movement_course"
        
        # Water Pool: SW quadrant (chunks -1 to -2, -1 to -2)
        if chunk_x in [-1, -2] and chunk_z in [-1, -2]:
            return "water_pool"
        
        # POI Zone: NW quadrant (chunks -1 to -2, 1-2)
        if chunk_x in [-1, -2] and chunk_z in [1, 2]:
            return "poi_zone"
        
        # Projectile Range: North (chunks 0, 2-3)
        if chunk_x == 0 and chunk_z in [2, 3]:
            return "projectile_range"
        
        return "default"
    
    def _generate_flat_terrain(self, chunk_x: int, chunk_z: int, chunk_size: int, voxel_grid: dict):
        """Generate basic flat terrain (3 layers to match world generator)."""
        for x in range(chunk_size):
            for z in range(chunk_size):
                # Surface
                voxel_grid[(x, self.base_height, z)] = "grass"
                # Dirt layers (subsurface only - no stone base needed)
                voxel_grid[(x, self.base_height - 1, z)] = "dirt"
                voxel_grid[(x, self.base_height - 2, z)] = "dirt"
    
    def _generate_spawn_hub(self, chunk_x: int, chunk_z: int, chunk_size: int, voxel_grid: dict, entities: list):
        """Generate central spawn area with visual markers."""
        self._generate_flat_terrain(chunk_x, chunk_z, chunk_size, voxel_grid)
        
        # Add spawn marker (colored blocks in a pattern)
        center = chunk_size // 2
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) == 2 or abs(dz) == 2:
                    x, z = center + dx, center + dz
                    if 0 <= x < chunk_size and 0 <= z < chunk_size:
                        voxel_grid[(x, self.base_height + 1, z)] = "stone_bricks"
    
    def _generate_combat_arena(self, chunk_x: int, chunk_z: int, chunk_size: int, voxel_grid: dict, entities: list):
        """Generate walled combat arena with enemy spawns."""
        self._generate_flat_terrain(chunk_x, chunk_z, chunk_size, voxel_grid)
        
        # Build walls on the perimeter of the 2x2 chunk area
        # Only build walls on outer edges
        is_edge_x = chunk_x in [1, 2]
        is_edge_z = chunk_z in [1, 2]
        
        for x in range(chunk_size):
            for z in range(chunk_size):
                world_x = chunk_x * chunk_size + x
                world_z = chunk_z * chunk_size + z
                
                # Check if on perimeter of combat zone (16-47 in both axes)
                on_wall = False
                if world_x in [16, 47] and 16 <= world_z <= 47:
                    on_wall = True
                if world_z in [16, 47] and 16 <= world_x <= 47:
                    on_wall = True
                
                if on_wall:
                    for h in range(1, 4):  # 3-block high walls
                        voxel_grid[(x, self.base_height + h, z)] = "stone_bricks"
        
        # Add enemy spawns in center chunk (1, 1)
        if chunk_x == 1 and chunk_z == 1:
            # 5 enemies in various positions
            spawn_positions = [
                (8, 8), (8, 12), (12, 8), (12, 12), (10, 10)
            ]
            for i, (sx, sz) in enumerate(spawn_positions):
                entities.append(("skeleton", chunk_x * chunk_size + sx, self.base_height + 1, chunk_z * chunk_size + sz, "red"))
    
    def _generate_movement_course(self, chunk_x: int, chunk_z: int, chunk_size: int, voxel_grid: dict, entities: list):
        """Generate varied terrain for movement testing."""
        self._generate_flat_terrain(chunk_x, chunk_z, chunk_size, voxel_grid)
        
        # Add stairs, platforms, and gaps
        for x in range(chunk_size):
            for z in range(chunk_size):
                world_x = chunk_x * chunk_size + x
                world_z = chunk_z * chunk_size + z
                
                # Staircase in first chunk
                if chunk_x == 1 and chunk_z == -1:
                    if 4 <= x <= 11 and 4 <= z <= 11:
                        # Rising staircase
                        height = self.base_height + ((x - 4) // 2)
                        for y in range(self.base_height, height + 1):
                            voxel_grid[(x, y, z)] = "stone"
                
                # Platforms with gaps in second chunk
                if chunk_x == 2 and chunk_z == -2:
                    # Create 3 platforms with gaps
                    if 2 <= x <= 5 and 2 <= z <= 13:
                        voxel_grid[(x, self.base_height + 2, z)] = "stone"
                    elif 8 <= x <= 11 and 2 <= z <= 13:
                        voxel_grid[(x, self.base_height + 2, z)] = "stone"
                    elif 14 <= x <= 15 and 2 <= z <= 13:
                        voxel_grid[(x, self.base_height + 2, z)] = "stone"
    
    def _generate_water_pool(self, chunk_x: int, chunk_z: int, chunk_size: int, voxel_grid: dict, entities: list):
        """Generate water pool for swimming tests."""
        # Lower base terrain
        pool_depth = 3
        
        for x in range(chunk_size):
            for z in range(chunk_size):
                world_x = chunk_x * chunk_size + x
                world_z = chunk_z * chunk_size + z
                
                # Create bowl-shaped pool
                dist_from_center = math.sqrt((world_x + 24) ** 2 + (world_z + 24) ** 2)
                
                if dist_from_center < 20:
                    # Inside pool area
                    pool_floor = self.base_height - pool_depth
                    
                    # Floor
                    voxel_grid[(x, pool_floor, z)] = "sand"
                    voxel_grid[(x, pool_floor - 1, z)] = "dirt"
                    for y in range(pool_floor - 2, -1, -1):
                        voxel_grid[(x, y, z)] = "stone"
                    
                    # Fill with water
                    for y in range(pool_floor + 1, self.base_height + 1):
                        voxel_grid[(x, y, z)] = "water"
                    
                    # Small island in center
                    if dist_from_center < 5:
                        for y in range(pool_floor + 1, self.base_height + 2):
                            voxel_grid[(x, y, z)] = "sand"
                else:
                    # Outside pool - normal terrain with slope down
                    self._generate_flat_terrain(chunk_x, chunk_z, chunk_size, voxel_grid)
    
    def _generate_poi_zone(self, chunk_x: int, chunk_z: int, chunk_size: int, voxel_grid: dict, entities: list, chest_loot: dict):
        """Generate POI testing area with shrine and camp."""
        self._generate_flat_terrain(chunk_x, chunk_z, chunk_size, voxel_grid)
        
        # Place shrine in chunk (-2, 2)
        if chunk_x == -2 and chunk_z == 2:
            self._place_poi(ShrineGenerator(self.world_seed), chunk_x, chunk_z, chunk_size, voxel_grid, entities, chest_loot)
        
        # Place camp in chunk (-1, 1)
        if chunk_x == -1 and chunk_z == 1:
            self._place_poi(CampGenerator(self.world_seed), chunk_x, chunk_z, chunk_size, voxel_grid, entities, chest_loot)
    
    def _generate_projectile_range(self, chunk_x: int, chunk_z: int, chunk_size: int, voxel_grid: dict, entities: list):
        """Generate long corridor for projectile testing."""
        self._generate_flat_terrain(chunk_x, chunk_z, chunk_size, voxel_grid)
        
        # Create walled corridor
        for x in range(chunk_size):
            for z in range(chunk_size):
                # Walls on sides (x = 4 and x = 11)
                if x in [4, 11]:
                    for h in range(1, 4):
                        voxel_grid[(x, self.base_height + h, z)] = "stone_bricks"
                
                # Target markers at far end
                if chunk_z == 3 and z > 12:
                    if x in [6, 7, 8, 9]:
                        voxel_grid[(x, self.base_height + 1, z)] = "wool_red"
                        voxel_grid[(x, self.base_height + 2, z)] = "wool_red"

    def _place_poi(self, generator, chunk_x, chunk_z, chunk_size, voxel_grid, entities_out, chest_loot_out):
        """Helper to place a POI in the center of the chunk."""
        center_x = chunk_x * chunk_size + (chunk_size // 2)
        center_z = chunk_z * chunk_size + (chunk_size // 2)
        base_y = self.base_height
        
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
        
        # Add chest loot if present
        if hasattr(poi_data, 'loot') and poi_data.loot:
            chest_loot_out.update(poi_data.loot)

    def get_height(self, x: float, z: float) -> float:
        """Return height for spawn system."""
        return float(self.base_height)

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
        load_radius=4,  # Match arena size (7x7 = radius 3, +1 for buffer)
        unload_radius=5,  # Slightly larger than load radius
        max_chunks_per_frame=10, # Load faster for small arena
        sea_level=0, 
        complex_water=complex_water
    )
