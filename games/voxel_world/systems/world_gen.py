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

        
        # Create NodePath for chunk and attach to render
        chunk_np = self.base.render.attachNewNode(geom_node)
        
        # Apply texture if available
        if self.texture_atlas and self.texture_atlas.is_loaded():
            chunk_np.setTexture(self.texture_atlas.get_texture())
        
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
    ):
        """Add collision polygons to chunk mesh.
        
        Creates collision geometry for the top faces of terrain blocks.
        This allows raycasting to detect ground height and surface normals.
        
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
        """Update terrain system.
        
        TODO: Implement dynamic chunk loading/unloading based on player position.
        For now, chunks are created manually via create_chunk().
        
        Args:
            dt: Delta time since last update
        """
        pass
