"""Terrain generation and chunk management system with collision support."""

from engine.ecs.system import System
from engine.rendering.mesh import MeshBuilder
from games.voxel_world.biomes.biomes import BiomeRegistry
from games.voxel_world.blocks.blocks import BlockRegistry
from panda3d.core import (
    NodePath, CollisionNode, CollisionPolygon, LVector3f,
    BitMask32
)
from typing import Dict, Tuple, Optional


class TerrainSystem(System):
    """Manages terrain generation, chunk loading, and collision geometry."""
    
    def __init__(self, world, event_bus, base, texture_atlas=None):
        super().__init__(world, event_bus)
        self.base = base
        self.texture_atlas = texture_atlas
        self.chunks: Dict[Tuple[int, int], NodePath] = {}
        self.chunk_size = 16
        
        # Dynamic loading configuration
        self.load_radius = 6  # Load chunks within 6 chunk radius (~96 blocks)
        self.unload_radius = 8  # Unload chunks beyond 8 chunk radius (2-chunk buffer)
        self.max_chunks_per_frame = 3  # Throttle loading for performance
        
        # Track last player position to optimize loading
        self.last_player_chunk: Optional[Tuple[int, int]] = None
        
        # Water configuration
        self.sea_level = 0  # Blocks below this height get water

        
    def get_height(self, x: float, z: float) -> float:
        """Get terrain height at world position using biome system.
        
        Args:
            x: World X coordinate
            z: World Z coordinate (depth/forward in Panda3D)
            
        Returns:
            Height (Y coordinate) at the given position
        """
        biome = BiomeRegistry.get_biome_at(x, z)
        return biome.get_height(x, z)
    
    def create_chunk(self, chunk_x: int, chunk_z: int) -> NodePath:
        """Generate a chunk with visual mesh and collision geometry.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            
        Returns:
            NodePath containing the chunk mesh and collision
        """
        # Generate heightmap and biome data
        heights = []
        biomes = []
        for x in range(self.chunk_size):
            heights.append([])
            biomes.append([])
            for z in range(self.chunk_size):
                world_x = chunk_x * self.chunk_size + x
                world_z = chunk_z * self.chunk_size + z
                biome = BiomeRegistry.get_biome_at(world_x, world_z)
                heights[x].append(int(biome.get_height(world_x, world_z)))
                biomes[x].append(biome)
        
        # Build visual mesh
        geom_node = MeshBuilder.build_chunk_mesh_with_callback(
            heights, biomes, chunk_x, chunk_z, self.chunk_size,
            self.texture_atlas,
            BlockRegistry,
            self.get_height
        )

        # Find water blocks (terrain below sea level)
        water_blocks = []
        for x in range(self.chunk_size):
            for z in range(self.chunk_size):
                terrain_height = heights[x][z]
                # Place water from terrain surface up to sea level (exclusive)
                # Water block at y has top face at y+1, so block at sea_level-1 has top at sea_level
                if terrain_height < self.sea_level:
                    for y in range(terrain_height, self.sea_level):
                        water_blocks.append((x, y, z))
        
        # Create NodePath for chunk and attach to render
        chunk_np = self.base.render.attachNewNode(geom_node)
        
        # Apply texture if available (BEFORE adding water to prevent inheritance)
        if self.texture_atlas and self.texture_atlas.is_loaded():
            chunk_np.setTexture(self.texture_atlas.get_texture())
        
        # Add water mesh if there are water blocks
        if water_blocks:
            water_node = MeshBuilder.build_water_mesh(
                water_blocks, chunk_x, chunk_z, self.chunk_size
            )
            if water_node:
                water_np = chunk_np.attachNewNode(water_node)
                # Enable transparency for water
                from panda3d.core import TransparencyAttrib
                water_np.setTransparency(TransparencyAttrib.MAlpha)
                # Clear texture on water (prevent inheritance from parent)
                water_np.clearTexture()
        
        # Add collision geometry
        self._add_collision_to_chunk(chunk_np, heights, chunk_x, chunk_z)
        
        # Store chunk reference
        self.chunks[(chunk_x, chunk_z)] = chunk_np

        
        return chunk_np
    
    def _add_collision_to_chunk(
        self, 
        chunk_np: NodePath, 
        heights: list, 
        chunk_x: int, 
        chunk_z: int
    ) -> None:
        """Add collision polygons to chunk mesh.
        
        Creates collision geometry for both top and side faces of terrain blocks.
        This allows raycasting to detect ground height, surface normals, and walls.
        
        Collision Layer System:
        - BitMask32.bit(1): Terrain collision layer
        - setFromCollideMask: What this node can collide WITH (for active colliders like rays)
        - setIntoCollideMask: What can collide INTO this node (terrain is passive, can be hit)
        
        Performance Note:
        - Side faces use non-greedy meshing (one polygon per block face)
        - Future optimization: Greedy meshing could merge adjacent vertical faces
        
        Args:
            chunk_np: NodePath to attach collision to
            heights: 2D array of block heights
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
        """
        cnode = CollisionNode(f'chunk_collision_{chunk_x}_{chunk_z}')
        cnode.setFromCollideMask(BitMask32.bit(1))  # Terrain collision layer
        cnode.setIntoCollideMask(BitMask32.bit(1))  # Can be collided with
        
        base_x = chunk_x * self.chunk_size
        base_z = chunk_z * self.chunk_size
        
        # Create collision polygons for top faces
        for x in range(self.chunk_size):
            for z in range(self.chunk_size):
                h = heights[x][z]
                world_x = base_x + x
                world_z = base_z + z
                
                # Create quad vertices (Panda3D: Z is up, Y is forward/depth)
                # Top face at height h
                v0 = LVector3f(world_x, world_z, h)
                v1 = LVector3f(world_x + 1, world_z, h)
                v2 = LVector3f(world_x + 1, world_z + 1, h)
                v3 = LVector3f(world_x, world_z + 1, h)
                
                # Add collision polygons (two triangles per quad)
                # Counter-clockwise winding for upward-facing normals
                cnode.addSolid(CollisionPolygon(v0, v1, v2))
                cnode.addSolid(CollisionPolygon(v0, v2, v3))
        
        # Create collision polygons for side faces
        # Only generate faces that are exposed (neighbor height is lower)
        for x in range(self.chunk_size):
            for z in range(self.chunk_size):
                h = heights[x][z]
                world_x = base_x + x
                world_z = base_z + z
                
                # Get neighbor heights (with bounds checking)
                # East neighbor (+X)
                if x + 1 < self.chunk_size:
                    h_east = heights[x + 1][z]
                else:
                    h_east = int(self.get_height(world_x + 1, world_z))
                
                # West neighbor (-X)
                if x - 1 >= 0:
                    h_west = heights[x - 1][z]
                else:
                    h_west = int(self.get_height(world_x - 1, world_z))
                
                # South neighbor (+Z)
                if z + 1 < self.chunk_size:
                    h_south = heights[x][z + 1]
                else:
                    h_south = int(self.get_height(world_x, world_z + 1))
                
                # North neighbor (-Z)
                if z - 1 >= 0:
                    h_north = heights[x][z - 1]
                else:
                    h_north = int(self.get_height(world_x, world_z - 1))
                
                # --- East side (+X) ---
                if h_east < h:
                    # Generate collision for each vertical layer
                    for y0 in range(h_east + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        
                        # Vertices for east-facing quad (counter-clockwise from outside)
                        sv0 = LVector3f(world_x + 1, world_z, y_bottom)
                        sv1 = LVector3f(world_x + 1, world_z + 1, y_bottom)
                        sv2 = LVector3f(world_x + 1, world_z + 1, y_top)
                        sv3 = LVector3f(world_x + 1, world_z, y_top)
                        
                        cnode.addSolid(CollisionPolygon(sv0, sv1, sv2))
                        cnode.addSolid(CollisionPolygon(sv0, sv2, sv3))
                
                # --- West side (-X) ---
                if h_west < h:
                    for y0 in range(h_west + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        
                        # Vertices for west-facing quad (counter-clockwise from outside)
                        sv0 = LVector3f(world_x, world_z + 1, y_bottom)
                        sv1 = LVector3f(world_x, world_z, y_bottom)
                        sv2 = LVector3f(world_x, world_z, y_top)
                        sv3 = LVector3f(world_x, world_z + 1, y_top)
                        
                        cnode.addSolid(CollisionPolygon(sv0, sv1, sv2))
                        cnode.addSolid(CollisionPolygon(sv0, sv2, sv3))
                
                # --- South side (+Z) ---
                if h_south < h:
                    for y0 in range(h_south + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        
                        # Vertices for south-facing quad (counter-clockwise from outside)
                        sv0 = LVector3f(world_x + 1, world_z + 1, y_bottom)
                        sv1 = LVector3f(world_x, world_z + 1, y_bottom)
                        sv2 = LVector3f(world_x, world_z + 1, y_top)
                        sv3 = LVector3f(world_x + 1, world_z + 1, y_top)
                        
                        cnode.addSolid(CollisionPolygon(sv0, sv1, sv2))
                        cnode.addSolid(CollisionPolygon(sv0, sv2, sv3))
                
                # --- North side (-Z) ---
                if h_north < h:
                    for y0 in range(h_north + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        
                        # Vertices for north-facing quad (counter-clockwise from outside)
                        sv0 = LVector3f(world_x, world_z, y_bottom)
                        sv1 = LVector3f(world_x + 1, world_z, y_bottom)
                        sv2 = LVector3f(world_x + 1, world_z, y_top)
                        sv3 = LVector3f(world_x, world_z, y_top)
                        
                        cnode.addSolid(CollisionPolygon(sv0, sv1, sv2))
                        cnode.addSolid(CollisionPolygon(sv0, sv2, sv3))
        
        # Attach collision node to chunk
        chunk_np.attachNewNode(cnode)

    
    def unload_chunk(self, chunk_x: int, chunk_z: int):
        """Remove a chunk from the world.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
        """
        chunk_key = (chunk_x, chunk_z)
        if chunk_key in self.chunks:
            chunk_np = self.chunks[chunk_key]
            chunk_np.removeNode()
            del self.chunks[chunk_key]
    
    def update(self, dt: float):
        """Update terrain system with dynamic chunk loading/unloading.
        
        Loads chunks in a radius around the player and unloads distant chunks
        to support exploration while managing memory.
        
        Args:
            dt: Delta time since last update
        """
        # Get player entity
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            return  # No player spawned yet
        
        from engine.components.core import Transform
        transform = self.world.get_component(player_id, Transform)
        if not transform:
            return
        
        # Calculate player's current chunk position
        # Panda3D: X and Y are horizontal, Z is vertical
        player_chunk_x = int(transform.position.x // self.chunk_size)
        player_chunk_z = int(transform.position.y // self.chunk_size)  # Y is depth in Panda3D
        player_chunk = (player_chunk_x, player_chunk_z)
        
        # Skip if player hasn't moved to a new chunk
        if player_chunk == self.last_player_chunk:
            return
        
        self.last_player_chunk = player_chunk
        
        # Determine chunks to load (circular radius around player)
        chunks_to_load = []
        for dx in range(-self.load_radius, self.load_radius + 1):
            for dz in range(-self.load_radius, self.load_radius + 1):
                # Circular radius check
                distance_sq = dx * dx + dz * dz
                if distance_sq <= self.load_radius * self.load_radius:
                    chunk_pos = (player_chunk_x + dx, player_chunk_z + dz)
                    
                    # Only queue if not already loaded
                    if chunk_pos not in self.chunks:
                        chunks_to_load.append((chunk_pos, distance_sq))
        
        # Sort by distance (load nearest chunks first)
        chunks_to_load.sort(key=lambda x: x[1])
        
        # Load chunks (throttled to prevent frame drops)
        chunks_loaded = 0
        for chunk_pos, _ in chunks_to_load:
            if chunks_loaded >= self.max_chunks_per_frame:
                break
            
            self.create_chunk(chunk_pos[0], chunk_pos[1])
            chunks_loaded += 1
        
        # Unload distant chunks (circular radius)
        chunks_to_unload = []
        for chunk_pos in self.chunks.keys():
            dx = chunk_pos[0] - player_chunk_x
            dz = chunk_pos[1] - player_chunk_z
            distance_sq = dx * dx + dz * dz
            
            # Unload if beyond unload radius
            if distance_sq > self.unload_radius * self.unload_radius:
                chunks_to_unload.append(chunk_pos)
        
        # Perform unloading
        for chunk_pos in chunks_to_unload:
            self.unload_chunk(chunk_pos[0], chunk_pos[1])
