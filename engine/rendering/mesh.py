from ursina import Vec3, Vec2, Mesh
from typing import List, Any, Optional

class MeshBuilder:
    """Handles generation of chunk meshes from heightmap data."""
    
    @staticmethod
    def build_chunk_mesh(
        heights: List[List[int]], 
        biomes: List[List[Any]], 
        chunk_x: int, 
        chunk_z: int, 
        chunk_size: int, 
        texture_atlas: Optional[Any],
        block_registry: Any
    ) -> Mesh:
        """Generate a Mesh object for a chunk based on heightmap and biome data.
        
        Args:
            heights: 2D array (chunk_size x chunk_size) of integer heights
            biomes: 2D array (chunk_size x chunk_size) of biome objects
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            chunk_size: Size of chunk (usually 16)
            texture_atlas: TextureAtlas instance (can be None)
            block_registry: BlockRegistry class/instance to look up block types
            
        Returns:
            ursina.Mesh: The generated mesh
        """
        base_x = chunk_x * chunk_size
        base_z = chunk_z * chunk_size

        vertices = []
        triangles = []
        uvs = []
        index = 0
        
        # Helper to get height safely (handling out of bounds by assuming adjacent chunks match edge?)
        # Actually, for side faces at chunk edges, we need neighbors.
        # The current design in world.py calls get_height() for neighbors.
        # To keep MeshBuilder pure, we either need 3x3 chunk data passed in, 
        # OR we accept a callback for "get_neighbor_height".
        # Let's use a callback for neighbor lookup to keep it simple and decoupled.
        
        # Wait, the previous implementation in world.py called self.get_height() for neighbors.
        # Let's add a callback argument: get_height_callback(world_x, world_z)
        pass 
    
    @staticmethod
    def build_chunk_mesh_with_callback(
        heights: List[List[int]], 
        biomes: List[List[Any]], 
        chunk_x: int, 
        chunk_z: int, 
        chunk_size: int, 
        texture_atlas: Optional[Any],
        block_registry: Any,
        get_height_callback: Any
    ) -> Mesh:
        """Generate a Mesh object with neighbor lookups via callback."""
        
        base_x = chunk_x * chunk_size
        base_z = chunk_z * chunk_size
        
        vertices = []
        triangles = []
        uvs = []
        index = 0

        # --- Top faces (simple 1x1 meshing) ---
        for z in range(chunk_size):
            for x in range(chunk_size):
                h = heights[x][z]
                world_x = base_x + x
                world_z = base_z + z

                # World-space rectangle (1x1 block)
                width = 1
                height_z = 1
                
                wx0 = world_x
                wx1 = world_x + 1
                wz0 = world_z
                wz1 = world_z + 1
                y = h

                v0 = Vec3(wx0, y, wz0)
                v1 = Vec3(wx1, y, wz0)
                v2 = Vec3(wx1, y, wz1)
                v3 = Vec3(wx0, y, wz1)

                vertices.extend([v0, v1, v2, v3])
                triangles.extend([
                    index, index + 1, index + 2,
                    index, index + 2, index + 3,
                ])
                
                # Get UVs for top face
                biome = biomes[x][z]
                surface_block = block_registry.get_block(biome.surface_block)
                tile_index = surface_block.get_face_tile('top')
                
                if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                    tile_uvs = texture_atlas.get_tiled_uvs(tile_index, width, height_z)
                    uvs.extend(tile_uvs)
                else:
                    uvs.extend([Vec2(0, 0), Vec2(1, 0), Vec2(1, 1), Vec2(0, 1)])
                
                index += 4

        # --- Side faces (non-greedy) ---
        for x in range(chunk_size):
            for z in range(chunk_size):
                h = heights[x][z]
                world_x = base_x + x
                world_z = base_z + z

                # Neighbor heights
                if x + 1 < chunk_size:
                    h_east = heights[x + 1][z]
                else:
                    h_east = get_height_callback(world_x + 1, world_z)

                if x - 1 >= 0:
                    h_west = heights[x - 1][z]
                else:
                    h_west = get_height_callback(world_x - 1, world_z)

                if z + 1 < chunk_size:
                    h_south = heights[x][z + 1]
                else:
                    h_south = get_height_callback(world_x, world_z + 1)

                if z - 1 >= 0:
                    h_north = heights[x][z - 1]
                else:
                    h_north = get_height_callback(world_x, world_z - 1)

                # --- East side (+X) ---
                if h_east < h:
                    for y0 in range(h_east + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        sv0 = Vec3(world_x + 1, y_bottom, world_z)
                        sv1 = Vec3(world_x + 1, y_bottom, world_z + 1)
                        sv2 = Vec3(world_x + 1, y_top,    world_z + 1)
                        sv3 = Vec3(world_x + 1, y_top,    world_z)
                        vertices.extend([sv0, sv1, sv2, sv3])
                        triangles.extend([index, index + 1, index + 2, index, index + 2, index + 3])
                        
                        biome = biomes[x][z]
                        surface_block = block_registry.get_block(biome.surface_block)
                        tile_index = surface_block.get_face_tile('side')
                        
                        if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                            uvs.extend(texture_atlas.get_tile_uvs(tile_index))
                        else:
                            uvs.extend([Vec2(0, 0), Vec2(1, 0), Vec2(1, 1), Vec2(0, 1)])
                        index += 4

                # --- West side (-X) ---
                if h_west < h:
                    for y0 in range(h_west + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        sv0 = Vec3(world_x, y_bottom, world_z + 1)
                        sv1 = Vec3(world_x, y_bottom, world_z)
                        sv2 = Vec3(world_x, y_top,    world_z)
                        sv3 = Vec3(world_x, y_top,    world_z + 1)
                        vertices.extend([sv0, sv1, sv2, sv3])
                        triangles.extend([index, index + 1, index + 2, index, index + 2, index + 3])
                        
                        biome = biomes[x][z]
                        surface_block = block_registry.get_block(biome.surface_block)
                        tile_index = surface_block.get_face_tile('side')
                        
                        if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                            uvs.extend(texture_atlas.get_tile_uvs(tile_index))
                        else:
                            uvs.extend([Vec2(0, 0), Vec2(1, 0), Vec2(1, 1), Vec2(0, 1)])
                        index += 4

                # --- South side (+Z) ---
                if h_south < h:
                    for y0 in range(h_south + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        sv0 = Vec3(world_x + 1, y_bottom, world_z + 1)
                        sv1 = Vec3(world_x,     y_bottom, world_z + 1)
                        sv2 = Vec3(world_x,     y_top,    world_z + 1)
                        sv3 = Vec3(world_x + 1, y_top,    world_z + 1)
                        vertices.extend([sv0, sv1, sv2, sv3])
                        triangles.extend([index, index + 1, index + 2, index, index + 2, index + 3])
                        
                        biome = biomes[x][z]
                        surface_block = block_registry.get_block(biome.surface_block)
                        tile_index = surface_block.get_face_tile('side')
                        
                        if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                            uvs.extend(texture_atlas.get_tile_uvs(tile_index))
                        else:
                            uvs.extend([Vec2(0, 0), Vec2(1, 0), Vec2(1, 1), Vec2(0, 1)])
                        index += 4

                # --- North side (-Z) ---
                if h_north < h:
                    for y0 in range(h_north + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        sv0 = Vec3(world_x,     y_bottom, world_z)
                        sv1 = Vec3(world_x + 1, y_bottom, world_z)
                        sv2 = Vec3(world_x + 1, y_top,    world_z)
                        sv3 = Vec3(world_x,     y_top,    world_z)
                        vertices.extend([sv0, sv1, sv2, sv3])
                        triangles.extend([index, index + 1, index + 2, index, index + 2, index + 3])
                        
                        biome = biomes[x][z]
                        surface_block = block_registry.get_block(biome.surface_block)
                        tile_index = surface_block.get_face_tile('side')
                        
                        if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                            uvs.extend(texture_atlas.get_tile_uvs(tile_index))
                        else:
                            uvs.extend([Vec2(0, 0), Vec2(1, 0), Vec2(1, 1), Vec2(0, 1)])
                        index += 4

        mesh = Mesh(vertices=vertices, triangles=triangles, uvs=uvs, mode='triangle')
        mesh.generate_normals()
        return mesh
