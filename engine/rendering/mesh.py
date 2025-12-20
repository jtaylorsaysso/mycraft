"""Procedural mesh generation for voxel terrain using Panda3D."""

from panda3d.core import (
    GeomNode, Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter,
    GeomTriangles, LVector3f, LVector2f, GeomVertexArrayFormat,
    InternalName, Geom as GeomEnums, TransparencyAttrib
)
from typing import List, Any, Optional, Tuple


class MeshBuilder:
    """Handles generation of chunk meshes from heightmap data using Panda3D."""
    
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
    ) -> GeomNode:
        """Generate a GeomNode for a chunk based on heightmap and biome data.
        
        Args:
            heights: 2D array (chunk_size x chunk_size) of integer heights
            biomes: 2D array (chunk_size x chunk_size) of biome objects
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            chunk_size: Size of chunk (usually 16)
            texture_atlas: TextureAtlas instance (can be None)
            block_registry: BlockRegistry class/instance to look up block types
            get_height_callback: Function(world_x, world_z) -> height for neighbors
            
        Returns:
            GeomNode: The generated mesh node
        """
        base_x = chunk_x * chunk_size
        base_z = chunk_z * chunk_size
        
        # Create vertex format (position + color + UV)
        vformat = GeomVertexFormat.getV3c4t2()
        vdata = GeomVertexData('chunk', vformat, Geom.UHStatic)
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        color_writer = GeomVertexWriter(vdata, 'color')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        
        # Triangle primitive
        tris = GeomTriangles(Geom.UHStatic)
        index = 0
        
        def get_ao_factor(x, z, h):
            """Simple AO calculation based on neighbor heights."""
            # Get neighbor heights (relative to chunk)
            def get_h(dx, dz):
                nx, nz = x + dx, z + dz
                if 0 <= nx < chunk_size and 0 <= nz < chunk_size:
                    return heights[nx][nz]
                return get_height_callback(base_x + nx, base_z + nz)

            # Check neighbors for each corner
            # Corner 0 (0,0)
            c0 = 0
            if get_h(-1, 0) >= h: c0 += 1
            if get_h(0, -1) >= h: c0 += 1
            if get_h(-1, -1) >= h: c0 += 1
            ao0 = 1.0 - (min(3, c0) * 0.2)

            # Corner 1 (1,0)
            c1 = 0
            if get_h(1, 0) >= h: c1 += 1
            if get_h(0, -1) >= h: c1 += 1
            if get_h(1, -1) >= h: c1 += 1
            ao1 = 1.0 - (min(3, c1) * 0.2)

            # Corner 2 (1,1)
            c2 = 0
            if get_h(1, 0) >= h: c2 += 1
            if get_h(0, 1) >= h: c2 += 1
            if get_h(1, 1) >= h: c2 += 1
            ao2 = 1.0 - (min(3, c2) * 0.2)

            # Corner 3 (0,1)
            c3 = 0
            if get_h(-1, 0) >= h: c3 += 1
            if get_h(0, 1) >= h: c3 += 1
            if get_h(-1, 1) >= h: c3 += 1
            ao3 = 1.0 - (min(3, c3) * 0.2)
            
            return [ao0, ao1, ao2, ao3]

        # --- Top faces (simple 1x1 meshing) ---
        for z in range(chunk_size):
            for x in range(chunk_size):
                h = heights[x][z]
                world_x = base_x + x
                world_z = base_z + z
                
                # World-space quad vertices
                v0 = LVector3f(world_x, world_z, h)
                v1 = LVector3f(world_x + 1, world_z, h)
                v2 = LVector3f(world_x + 1, world_z + 1, h)
                v3 = LVector3f(world_x, world_z + 1, h)
                
                # Add vertices
                vertex.addData3(v0)
                vertex.addData3(v1)
                vertex.addData3(v2)
                vertex.addData3(v3)
                
                # Add AO colors
                aos = get_ao_factor(x, z, h)
                for ao in aos:
                    color_writer.addData4(ao, ao, ao, 1.0)
                
                # Get UVs for top face
                biome = biomes[x][z]
                surface_block = block_registry.get_block(biome.surface_block)
                tile_index = surface_block.get_face_tile('top')
                
                if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                    tile_uvs = texture_atlas.get_tiled_uvs(tile_index, 1, 1)
                    for uv in tile_uvs:
                        texcoord.addData2(uv)
                else:
                    # Fallback UVs
                    texcoord.addData2(LVector2f(0, 0))
                    texcoord.addData2(LVector2f(1, 0))
                    texcoord.addData2(LVector2f(1, 1))
                    texcoord.addData2(LVector2f(0, 1))
                
                # Add triangles (two triangles per quad)
                tris.addVertices(index, index + 1, index + 2)
                tris.addVertices(index, index + 2, index + 3)
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
                
                biome = biomes[x][z]
                surface_block = block_registry.get_block(biome.surface_block)
                tile_index = surface_block.get_face_tile('side')
                
                # --- East side (+X) ---
                if h_east < h:
                    for y0 in range(h_east + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        
                        sv0 = LVector3f(world_x + 1, world_z, y_bottom)
                        sv1 = LVector3f(world_x + 1, world_z + 1, y_bottom)
                        sv2 = LVector3f(world_x + 1, world_z + 1, y_top)
                        sv3 = LVector3f(world_x + 1, world_z, y_top)
                        
                        vertex.addData3(sv0)
                        vertex.addData3(sv1)
                        vertex.addData3(sv2)
                        vertex.addData3(sv3)
                        
                        # Side AO (simplified: bottom is darker)
                        color_writer.addData4(0.7, 0.7, 0.7, 1.0)
                        color_writer.addData4(0.7, 0.7, 0.7, 1.0)
                        color_writer.addData4(1.0, 1.0, 1.0, 1.0)
                        color_writer.addData4(1.0, 1.0, 1.0, 1.0)
                        
                        if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                            tile_uvs = texture_atlas.get_tile_uvs(tile_index)
                            for uv in tile_uvs:
                                texcoord.addData2(uv)
                        else:
                            texcoord.addData2(LVector2f(0, 0))
                            texcoord.addData2(LVector2f(1, 0))
                            texcoord.addData2(LVector2f(1, 1))
                            texcoord.addData2(LVector2f(0, 1))
                        
                        tris.addVertices(index, index + 1, index + 2)
                        tris.addVertices(index, index + 2, index + 3)
                        index += 4
                
                # --- West side (-X) ---
                if h_west < h:
                    for y0 in range(h_west + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        
                        sv0 = LVector3f(world_x, world_z + 1, y_bottom)
                        sv1 = LVector3f(world_x, world_z, y_bottom)
                        sv2 = LVector3f(world_x, world_z, y_top)
                        sv3 = LVector3f(world_x, world_z + 1, y_top)
                        
                        vertex.addData3(sv0)
                        vertex.addData3(sv1)
                        vertex.addData3(sv2)
                        vertex.addData3(sv3)
                        
                        color_writer.addData4(0.7, 0.7, 0.7, 1.0)
                        color_writer.addData4(0.7, 0.7, 0.7, 1.0)
                        color_writer.addData4(1.0, 1.0, 1.0, 1.0)
                        color_writer.addData4(1.0, 1.0, 1.0, 1.0)
                        
                        if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                            tile_uvs = texture_atlas.get_tile_uvs(tile_index)
                            for uv in tile_uvs:
                                texcoord.addData2(uv)
                        else:
                            texcoord.addData2(LVector2f(0, 0))
                            texcoord.addData2(LVector2f(1, 0))
                            texcoord.addData2(LVector2f(1, 1))
                            texcoord.addData2(LVector2f(0, 1))
                        
                        tris.addVertices(index, index + 1, index + 2)
                        tris.addVertices(index, index + 2, index + 3)
                        index += 4
                
                # --- South side (+Z) ---
                if h_south < h:
                    for y0 in range(h_south + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        
                        sv0 = LVector3f(world_x + 1, world_z + 1, y_bottom)
                        sv1 = LVector3f(world_x, world_z + 1, y_bottom)
                        sv2 = LVector3f(world_x, world_z + 1, y_top)
                        sv3 = LVector3f(world_x + 1, world_z + 1, y_top)
                        
                        vertex.addData3(sv0)
                        vertex.addData3(sv1)
                        vertex.addData3(sv2)
                        vertex.addData3(sv3)
                        
                        color_writer.addData4(0.7, 0.7, 0.7, 1.0)
                        color_writer.addData4(0.7, 0.7, 0.7, 1.0)
                        color_writer.addData4(1.0, 1.0, 1.0, 1.0)
                        color_writer.addData4(1.0, 1.0, 1.0, 1.0)
                        
                        if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                            tile_uvs = texture_atlas.get_tile_uvs(tile_index)
                            for uv in tile_uvs:
                                texcoord.addData2(uv)
                        else:
                            texcoord.addData2(LVector2f(0, 0))
                            texcoord.addData2(LVector2f(1, 0))
                            texcoord.addData2(LVector2f(1, 1))
                            texcoord.addData2(LVector2f(0, 1))
                        
                        tris.addVertices(index, index + 1, index + 2)
                        tris.addVertices(index, index + 2, index + 3)
                        index += 4
                
                # --- North side (-Z) ---
                if h_north < h:
                    for y0 in range(h_north + 1, h + 1):
                        y_bottom = y0 - 1
                        y_top = y0
                        
                        sv0 = LVector3f(world_x, world_z, y_bottom)
                        sv1 = LVector3f(world_x + 1, world_z, y_bottom)
                        sv2 = LVector3f(world_x + 1, world_z, y_top)
                        sv3 = LVector3f(world_x, world_z, y_top)
                        
                        vertex.addData3(sv0)
                        vertex.addData3(sv1)
                        vertex.addData3(sv2)
                        vertex.addData3(sv3)
                        
                        color_writer.addData4(0.7, 0.7, 0.7, 1.0)
                        color_writer.addData4(0.7, 0.7, 0.7, 1.0)
                        color_writer.addData4(1.0, 1.0, 1.0, 1.0)
                        color_writer.addData4(1.0, 1.0, 1.0, 1.0)
                        
                        if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                            tile_uvs = texture_atlas.get_tile_uvs(tile_index)
                            for uv in tile_uvs:
                                texcoord.addData2(uv)
                        else:
                            texcoord.addData2(LVector2f(0, 0))
                            texcoord.addData2(LVector2f(1, 0))
                            texcoord.addData2(LVector2f(1, 1))
                            texcoord.addData2(LVector2f(0, 1))
                        
                        tris.addVertices(index, index + 1, index + 2)
                        tris.addVertices(index, index + 2, index + 3)
                        index += 4
        
        # Create Geom and GeomNode
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        
        node = GeomNode('chunk_mesh')
        node.addGeom(geom)
        
        return node
    
    @staticmethod
    def build_water_mesh(
        water_blocks: List[Tuple[int, int, int]],
        chunk_x: int,
        chunk_z: int,
        chunk_size: int = 16
    ) -> Optional[GeomNode]:
        """Generate a mesh for water blocks with wobble shader support.
        
        Args:
            water_blocks: List of (x, y, z) positions of water blocks in chunk (local coords)
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            chunk_size: Size of chunk (default 16)
            
        Returns:
            GeomNode with water mesh, or None if no water blocks
        """
        if not water_blocks:
            return None
            
        # Create custom vertex format with block_id attribute
        vformat = GeomVertexFormat()
        
        # Add standard V3c4t2 arrays
        standard_format = GeomVertexFormat.getV3c4t2()
        vformat.addArray(standard_format.getArray(0))
        
        # Add custom block_id array for wobble phase
        array = GeomVertexArrayFormat()
        array.addColumn(InternalName.make("block_id"), 3, GeomEnums.NT_float32, GeomEnums.C_other)
        vformat.addArray(array)
        
        vformat = GeomVertexFormat.registerFormat(vformat)
        
        vdata = GeomVertexData('water', vformat, Geom.UHDynamic)  # Dynamic for animation
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        color_writer = GeomVertexWriter(vdata, 'color')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        block_id_writer = GeomVertexWriter(vdata, 'block_id')
        
        tris = GeomTriangles(Geom.UHStatic)
        index = 0
        
        # Convert list to set for fast lookup
        water_set = set(water_blocks)
        
        base_x = chunk_x * chunk_size
        base_z = chunk_z * chunk_size
        
        # Water color (cyan-blue)
        water_color = LVector3f(0.2, 0.5, 0.8)
        
        for (x, y, z) in water_blocks:
            world_x = base_x + x
            world_y = y
            world_z = base_z + z
            
            # Check neighbors for face culling
            neighbors = {
                'top': (x, y + 1, z),
                'bottom': (x, y - 1, z),
                'north': (x, y, z - 1),
                'south': (x, y, z + 1),
                'east': (x + 1, y, z),
                'west': (x - 1, y, z),
            }
            
            # Only render faces that are exposed (not touching other water)
            for face_name, neighbor_pos in neighbors.items():
                if neighbor_pos in water_set:
                    continue  # Skip face if neighbor is also water
                
                # Generate face vertices
                if face_name == 'top':
                    v0 = LVector3f(world_x, world_z, world_y + 1)
                    v1 = LVector3f(world_x + 1, world_z, world_y + 1)
                    v2 = LVector3f(world_x + 1, world_z + 1, world_y + 1)
                    v3 = LVector3f(world_x, world_z + 1, world_y + 1)
                elif face_name == 'bottom':
                    v0 = LVector3f(world_x, world_z + 1, world_y)
                    v1 = LVector3f(world_x + 1, world_z + 1, world_y)
                    v2 = LVector3f(world_x + 1, world_z, world_y)
                    v3 = LVector3f(world_x, world_z, world_y)
                elif face_name == 'north':
                    v0 = LVector3f(world_x, world_z, world_y)
                    v1 = LVector3f(world_x + 1, world_z, world_y)
                    v2 = LVector3f(world_x + 1, world_z, world_y + 1)
                    v3 = LVector3f(world_x, world_z, world_y + 1)
                elif face_name == 'south':
                    v0 = LVector3f(world_x + 1, world_z + 1, world_y)
                    v1 = LVector3f(world_x, world_z + 1, world_y)
                    v2 = LVector3f(world_x, world_z + 1, world_y + 1)
                    v3 = LVector3f(world_x + 1, world_z + 1, world_y + 1)
                elif face_name == 'east':
                    v0 = LVector3f(world_x + 1, world_z, world_y)
                    v1 = LVector3f(world_x + 1, world_z + 1, world_y)
                    v2 = LVector3f(world_x + 1, world_z + 1, world_y + 1)
                    v3 = LVector3f(world_x + 1, world_z, world_y + 1)
                else:  # west
                    v0 = LVector3f(world_x, world_z + 1, world_y)
                    v1 = LVector3f(world_x, world_z, world_y)
                    v2 = LVector3f(world_x, world_z, world_y + 1)
                    v3 = LVector3f(world_x, world_z + 1, world_y + 1)
                
                # Add vertices
                for v in [v0, v1, v2, v3]:
                    vertex.addData3(v)
                    color_writer.addData4(water_color.x, water_color.y, water_color.z, 0.7)
                    texcoord.addData2(LVector2f(0, 0))  # Dummy UVs
                    block_id_writer.addData3(world_x, world_y, world_z)
                
                # Add triangles
                tris.addVertices(index, index + 1, index + 2)
                tris.addVertices(index, index + 2, index + 3)
                index += 4
        
        if index == 0:
            return None  # No faces generated
        
        # Create Geom and GeomNode
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        
        node = GeomNode('water_mesh')
        node.addGeom(geom)
        
        return node
