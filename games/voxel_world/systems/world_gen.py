"""Terrain generation for voxel_world game.

This module implements the ChunkGenerator protocol for voxel_world,
delegating chunk streaming to the engine's ChunkManager.
"""

from typing import Dict, Tuple, Any, List

from games.voxel_world.biomes.biomes import BiomeRegistry
from games.voxel_world.blocks.blocks import BlockRegistry
from games.voxel_world.structures import *
from games.voxel_world.structures.biome_structures import get_structure_generators_for_biome
from games.voxel_world.pois import POIData, POIGenerator
from games.voxel_world.pois.shrine_generator import ShrineGenerator
from games.voxel_world.pois.camp_generator import CampGenerator
from games.voxel_world.biomes.noise import get_noise


class VoxelWorldGenerator:
    """ChunkGenerator implementation for voxel_world.
    
    Handles biome-based terrain generation and structure placement.
    Streaming and collision are handled by ChunkManager.
    """
    
    def __init__(self, seed: int = 0):
        """Initialize generator.
        
        Args:
            seed: World seed for deterministic generation
        """
        self.world_seed = seed
        self._structure_cache: Dict[Tuple[str, int], Any] = {}
        self._pois: List[POIData] = []  # Track spawned POIs
        self._poi_generators: List[POIGenerator] = []  # Registered generators
    
    def generate_chunk(
        self, 
        chunk_x: int, 
        chunk_z: int,
        chunk_size: int
    ) -> Tuple[Dict[Tuple[int, int, int], str], List[Tuple[str, int, int, int]]]:
        """Generate voxel grid and entities for a chunk.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            chunk_size: Size of chunk in blocks
            
        Returns:
            Tuple containing:
            - Dict mapping (local_x, y, local_z) -> block_name
            - List of entities to spawn (type, x, y, z)
        """
        # 1. Generate heightmap and biome data
        heights = []
        biomes = []
        for x in range(chunk_size):
            heights.append([])
            biomes.append([])
            for z in range(chunk_size):
                world_x = chunk_x * chunk_size + x
                world_z = chunk_z * chunk_size + z
                biome = BiomeRegistry.get_biome_at(world_x, world_z)
                heights[x].append(int(biome.get_height(world_x, world_z)))
                biomes[x].append(biome)
        
        # 2. Create voxel grid from heightmap
        voxel_grid = self._create_voxel_grid(heights, biomes, chunk_size)
        
        # 3. Add structures (trees, boulders, etc.)
        self._add_structures_to_grid(voxel_grid, chunk_x, chunk_z, biomes, heights, chunk_size)
        
        # 4. Add Points of Interest
        entities = self._add_pois_to_chunk(chunk_x, chunk_z, voxel_grid, biomes, heights, chunk_size)
        
        return voxel_grid, entities
    
    def get_height(self, x: float, z: float) -> float:
        """Get terrain height at world position.
        
        Args:
            x: World X coordinate
            z: World Z coordinate
            
        Returns:
            Height at this position
        """
        biome = BiomeRegistry.get_biome_at(x, z)
        return biome.get_height(x, z)
    
    def get_block_registry(self) -> Any:
        """Get block registry for property lookups."""
        return BlockRegistry
    
    def _create_voxel_grid(
        self, 
        heights: list, 
        biomes: list,
        chunk_size: int
    ) -> Dict[Tuple[int, int, int], str]:
        """Create terrain voxel grid from heightmap.
        
        Args:
            heights: 2D array of heights
            biomes: 2D array of biome objects
            chunk_size: Size of chunk
            
        Returns:
            Voxel grid dict
        """
        grid = {}
        
        for x in range(chunk_size):
            for z in range(chunk_size):
                h = heights[x][z]
                biome = biomes[x][z]
                
                # Surface block
                grid[(x, h, z)] = biome.surface_block
                
                # Subsurface layers (2 blocks down)
                for y in range(h - 1, h - 3, -1):
                    grid[(x, y, z)] = biome.subsurface_block
        
        return grid
    
    def _add_structures_to_grid(
        self,
        voxel_grid: Dict[Tuple[int, int, int], str],
        chunk_x: int,
        chunk_z: int,
        biomes: list,
        heights: list,
        chunk_size: int
    ):
        """Add structures (trees, rocks, etc.) to voxel grid.
        
        Args:
            voxel_grid: Grid to modify in-place
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            biomes: 2D array of biome objects
            heights: 2D array of heights
            chunk_size: Chunk size
        """
        for x in range(chunk_size):
            for z in range(chunk_size):
                biome = biomes[x][z]
                
                # Get configured generators for this biome
                gen_configs = get_structure_generators_for_biome(biome.name)
                
                for gen_name, config in gen_configs:
                    # Get/create generator instance
                    cache_key = (gen_name, self.world_seed)
                    if cache_key not in self._structure_cache:
                        if gen_name in globals():
                            gen_class = globals()[gen_name]
                            kwargs = {k: v for k, v in config.items() 
                                     if k not in ['density', 'scale', 'spacing']}
                            self._structure_cache[cache_key] = gen_class(seed=self.world_seed, **kwargs)
                        else:
                            continue
                    
                    generator = self._structure_cache[cache_key]
                    
                    # Check placement
                    world_x = chunk_x * chunk_size + x
                    world_z = chunk_z * chunk_size + z
                    
                    density = config.get('density', 0.05)
                    scale = config.get('scale', 0.2)
                    spacing = config.get('spacing', 3)
                    
                    # Spacing check
                    if x % spacing != 0 or z % spacing != 0:
                        continue
                    
                    if generator.should_generate_at(world_x, world_z, density, scale):
                        h = heights[x][z]
                        structure = generator.generate_structure(
                            world_x, h, world_z,
                            height_callback=self.get_height
                        )
                        
                        if structure:
                            for bx, by, bz, bname in structure.blocks:
                                # Convert to chunk-local
                                rx = bx - (chunk_x * chunk_size)
                                rz = bz - (chunk_z * chunk_size)
                                
                                # Only add if within bounds
                                if 0 <= rx < chunk_size and 0 <= rz < chunk_size:
                                    voxel_grid[(rx, by, rz)] = bname

    def _add_pois_to_chunk(
        self,
        chunk_x: int, 
        chunk_z: int, 
        voxel_grid: Dict[Tuple[int, int, int], str],
        biomes: list, 
        heights: list,
        chunk_size: int
    ):
        """Try to spawn POIs in this chunk."""
        # Simple spawn chance check using noise
        # Scale 0.01 = large features, ensuring POIs are spaced out
        poi_noise = get_noise(chunk_x * 100, chunk_z * 100, scale=0.01, octaves=1)
        
        # ~8% spawn chance (customizable)
        if poi_noise > 0.92:
            # Deterministic POI selection
            # Use distinct prime multipliers to mix up pattern relative to coordinates
            val = (chunk_x * 73 + chunk_z * 31) % 100
            
            if val < 60:
                generator = ShrineGenerator(self.world_seed)
            else:
                generator = CampGenerator(self.world_seed)
            
            if generator.should_spawn_at(chunk_x, chunk_z):
                # Attempt to find position
                pos = generator.get_spawn_position(
                    chunk_x, chunk_z, chunk_size, biomes, self.get_height
                )
                
                if pos:
                    wx, wy, wz = pos
                    
                    # Flatten terrain
                    generator.flatten_terrain(
                        wx, wz, wy, 3, voxel_grid, chunk_x, chunk_z, chunk_size
                    )
                    
                    # Generate structure
                    poi_data = generator.generate(wx, wy, wz, self.world_seed)
                    
                    # Add blocks to grid
                    for bx, by, bz, bname in poi_data.blocks:
                        # Convert to chunk-local
                        rx = bx - (chunk_x * chunk_size)
                        rz = bz - (chunk_z * chunk_size)
                        
                        if 0 <= rx < chunk_size and 0 <= rz < chunk_size:
                            voxel_grid[(rx, by, rz)] = bname
                            
                    # Track POI
                    self._pois.append(poi_data)
                    return poi_data.entities
        
        return []



def create_terrain_system(world, event_bus, base, texture_atlas=None, seed=0):
    """Factory function to create terrain system for voxel_world.
    
    Creates a VoxelWorldGenerator and wraps it with the engine's ChunkManager.
    
    Args:
        world: ECS World instance
        event_bus: Event bus
        base: Panda3D ShowBase instance
        texture_atlas: Optional TextureAtlas
        seed: World seed
        
    Returns:
        ChunkManager configured for voxel_world
    """
    from engine.world.chunk_manager import ChunkManager
    
    generator = VoxelWorldGenerator(seed=seed)
    
    # Get config if available
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
        max_chunks_per_frame=3,
        sea_level=0,
        complex_water=complex_water
    )


# Backward compatibility alias
TerrainSystem = None  # Use create_terrain_system() instead
