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
    def build_chunk_mesh_from_grid(
        voxel_grid: dict, 
        chunk_x: int, 
        chunk_z: int, 
        chunk_size: int, 
        texture_atlas: Optional[Any],
        block_registry: Any
    ) -> GeomNode:
        """Generate mesh from a sparse voxel grid (dictionary).
        
        Uses chunk-local coordinates (0 to chunk_size).
        The chunk NodePath will be positioned at world coordinates.
        
        Args:
            voxel_grid: Dict mapping (x, y, z) -> block_name (local coords)
            chunk_x: Chunk X coordinate (unused, for compatibility)
            chunk_z: Chunk Z coordinate (unused, for compatibility)
            chunk_size: Size of chunk
            texture_atlas: TextureAtlas instance
            block_registry: BlockRegistry for property lookups
            
        Returns:
            GeomNode: The generated mesh node
        """
        
        # Create vertex format (position + color + UV)
        vformat = GeomVertexFormat.getV3c4t2()
        vdata = GeomVertexData('chunk', vformat, Geom.UHStatic)
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        color_writer = GeomVertexWriter(vdata, 'color')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        
        tris = GeomTriangles(Geom.UHStatic)
        index = 0
        
        # Directions for neighbor checks
        directions = [
            (0, 1, 0, 'top'),
            (0, -1, 0, 'bottom'),
            (0, 0, -1, 'north'),
            (0, 0, 1, 'south'),
            (1, 0, 0, 'east'),
            (-1, 0, 0, 'west')
        ]
        
        # Iterate over all blocks in the sparse grid
        # Note: This renders everything in the grid.
        # Ensure grid only contains this chunk's blocks!
        for pos, block_name in voxel_grid.items():
            x, y, z = pos
            
            # Simple bounds check (should be handled by caller, but good safety)
            # if not (0 <= x < chunk_size and 0 <= z < chunk_size):
            #     continue
                
            block_def = block_registry.get_block(block_name)
            if not block_def:
                continue
                
            # Use local coordinates directly (no world offset)
            
            # Check 6 faces
            for dx, dy, dz, face_name in directions:
                nx, ny, nz = x + dx, y + dy, z + dz
                neighbor_pos = (nx, ny, nz)
                
                # Check if face is exposed
                # Exposed if:
                # 1. Neighbor is not in grid (empty air)
                # 2. Neighbor is transparent (e.g. leaves, glass) - Future improvement
                # For now, just check existence
                if neighbor_pos in voxel_grid:
                    neighbor_name = voxel_grid[neighbor_pos]
                    neighbor_def = block_registry.get_block(neighbor_name)
                    # Optimization: If neighbor is solid, cull face.
                    # TODO: Add transparency support (leaves shouldn't cull solid blocks)
                    if neighbor_name != "leaves" and neighbor_name != "water": 
                         continue

                # Use simple AO: 1.0 (optimize later)
                ao = 1.0
                
                # Vertices in chunk-local Panda3D coords (x, z, y)
                # x=horizontal, y=height(Z), z=horizontal(depth/Y)
                
                if face_name == 'top':
                    v0 = LVector3f(x, z, y + 1)
                    v1 = LVector3f(x + 1, z, y + 1)
                    v2 = LVector3f(x + 1, z + 1, y + 1)
                    v3 = LVector3f(x, z + 1, y + 1)
                elif face_name == 'bottom':
                    v0 = LVector3f(x, z + 1, y)
                    v1 = LVector3f(x + 1, z + 1, y)
                    v2 = LVector3f(x + 1, z, y)
                    v3 = LVector3f(x, z, y)
                elif face_name == 'north': # -Z direction in grid -> -Y in Panda
                    v0 = LVector3f(x, z, y)
                    v1 = LVector3f(x + 1, z, y)
                    v2 = LVector3f(x + 1, z, y + 1)
                    v3 = LVector3f(x, z, y + 1)
                elif face_name == 'south': # +Z direction -> +Y
                    v0 = LVector3f(x + 1, z + 1, y)
                    v1 = LVector3f(x, z + 1, y)
                    v2 = LVector3f(x, z + 1, y + 1)
                    v3 = LVector3f(x + 1, z + 1, y + 1)
                elif face_name == 'east': # +X
                    v0 = LVector3f(x + 1, z, y)
                    v1 = LVector3f(x + 1, z + 1, y)
                    v2 = LVector3f(x + 1, z + 1, y + 1)
                    v3 = LVector3f(x + 1, z, y + 1)
                elif face_name == 'west': # -X
                    v0 = LVector3f(x, z + 1, y)
                    v1 = LVector3f(x, z, y)
                    v2 = LVector3f(x, z, y + 1)
                    v3 = LVector3f(x, z + 1, y + 1)

                vertex.addData3(v0)
                vertex.addData3(v1)
                vertex.addData3(v2)
                vertex.addData3(v3)
                
                # Colors
                color_writer.addData4(ao, ao, ao, 1.0)
                color_writer.addData4(ao, ao, ao, 1.0)
                color_writer.addData4(ao, ao, ao, 1.0)
                color_writer.addData4(ao, ao, ao, 1.0)

                # UVs
                lookup_face = face_name
                if face_name in ['north', 'south', 'east', 'west']:
                    lookup_face = 'side'
                    
                tile_index = block_def.get_face_tile(lookup_face)
                if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                    tile_uvs = texture_atlas.get_tile_uvs(tile_index)
                    for uv in tile_uvs:
                        texcoord.addData2(uv)
                else:
                    # Fallback
                    texcoord.addData2(LVector2f(0, 0))
                    texcoord.addData2(LVector2f(1, 0))
                    texcoord.addData2(LVector2f(1, 1))
                    texcoord.addData2(LVector2f(0, 1))

                tris.addVertices(index, index + 1, index + 2)
                tris.addVertices(index, index + 2, index + 3)
                index += 4
        
        if index == 0:
            return GeomNode('empty_chunk')

        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode('chunk_mesh')
        node.addGeom(geom)
        return node

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
        
        # --- Side faces (GREEDY: single merged quad per height difference) ---
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
                
                # --- East side (+X) --- GREEDY: single merged quad for full height
                if h_east < h:
                    face_height = h - h_east
                    y_bottom = h_east
                    y_top = h
                    
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
                    
                    # Use tiled UVs so texture repeats vertically
                    if tile_index is not None and texture_atlas and texture_atlas.is_loaded():
                        tile_uvs = texture_atlas.get_tiled_uvs(tile_index, 1, face_height)
                        for uv in tile_uvs:
                            texcoord.addData2(uv)
                    else:
                        texcoord.addData2(LVector2f(0, 0))
                        texcoord.addData2(LVector2f(1, 0))
                        texcoord.addData2(LVector2f(1, face_height))
                        texcoord.addData2(LVector2f(0, face_height))
                    
                    tris.addVertices(index, index + 1, index + 2)
                    tris.addVertices(index, index + 2, index + 3)
                    index += 4
                
                # --- West side (-X) --- GREEDY: single merged quad for full height
                if h_west < h:
                    face_height = h - h_west
                    y_bottom = h_west
                    y_top = h
                    
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
                        tile_uvs = texture_atlas.get_tiled_uvs(tile_index, 1, face_height)
                        for uv in tile_uvs:
                            texcoord.addData2(uv)
                    else:
                        texcoord.addData2(LVector2f(0, 0))
                        texcoord.addData2(LVector2f(1, 0))
                        texcoord.addData2(LVector2f(1, face_height))
                        texcoord.addData2(LVector2f(0, face_height))
                    
                    tris.addVertices(index, index + 1, index + 2)
                    tris.addVertices(index, index + 2, index + 3)
                    index += 4
                
                # --- South side (+Z) --- GREEDY: single merged quad for full height
                if h_south < h:
                    face_height = h - h_south
                    y_bottom = h_south
                    y_top = h
                    
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
                        tile_uvs = texture_atlas.get_tiled_uvs(tile_index, 1, face_height)
                        for uv in tile_uvs:
                            texcoord.addData2(uv)
                    else:
                        texcoord.addData2(LVector2f(0, 0))
                        texcoord.addData2(LVector2f(1, 0))
                        texcoord.addData2(LVector2f(1, face_height))
                        texcoord.addData2(LVector2f(0, face_height))
                    
                    tris.addVertices(index, index + 1, index + 2)
                    tris.addVertices(index, index + 2, index + 3)
                    index += 4
                
                # --- North side (-Z) --- GREEDY: single merged quad for full height
                if h_north < h:
                    face_height = h - h_north
                    y_bottom = h_north
                    y_top = h
                    
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
                        tile_uvs = texture_atlas.get_tiled_uvs(tile_index, 1, face_height)
                        for uv in tile_uvs:
                            texcoord.addData2(uv)
                    else:
                        texcoord.addData2(LVector2f(0, 0))
                        texcoord.addData2(LVector2f(1, 0))
                        texcoord.addData2(LVector2f(1, face_height))
                        texcoord.addData2(LVector2f(0, face_height))
                    
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
        
        # Water color (cyan-blue)
        water_color = LVector3f(0.2, 0.5, 0.8)
        
        for (x, y, z) in water_blocks:
            # water_blocks contains (local_x, height, local_z) coordinates
            # Use local coordinates directly
            height = y  # This is the actual height (Panda3D Z axis)
            
            # Check neighbors for face culling (in chunk-local coords)
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
                
                # Generate face vertices in Panda3D coords (X, Y_depth, Z_height)
                # Using local coordinates
                if face_name == 'top':
                    v0 = LVector3f(x, z, height + 1)
                    v1 = LVector3f(x + 1, z, height + 1)
                    v2 = LVector3f(x + 1, z + 1, height + 1)
                    v3 = LVector3f(x, z + 1, height + 1)
                elif face_name == 'bottom':
                    v0 = LVector3f(x, z + 1, height)
                    v1 = LVector3f(x + 1, z + 1, height)
                    v2 = LVector3f(x + 1, z, height)
                    v3 = LVector3f(x, z, height)
                elif face_name == 'north':
                    v0 = LVector3f(x, z, height)
                    v1 = LVector3f(x + 1, z, height)
                    v2 = LVector3f(x + 1, z, height + 1)
                    v3 = LVector3f(x, z, height + 1)
                elif face_name == 'south':
                    v0 = LVector3f(x + 1, z + 1, height)
                    v1 = LVector3f(x, z + 1, height)
                    v2 = LVector3f(x, z + 1, height + 1)
                    v3 = LVector3f(x + 1, z + 1, height + 1)
                elif face_name == 'east':
                    v0 = LVector3f(x + 1, z, height)
                    v1 = LVector3f(x + 1, z + 1, height)
                    v2 = LVector3f(x + 1, z + 1, height + 1)
                    v3 = LVector3f(x + 1, z, height + 1)
                else:  # west
                    v0 = LVector3f(x, z + 1, height)
                    v1 = LVector3f(x, z, height)
                    v2 = LVector3f(x, z, height + 1)
                    v3 = LVector3f(x, z + 1, height + 1)
                
                # Add vertices
                for v in [v0, v1, v2, v3]:
                    vertex.addData3(v)
                    color_writer.addData4(water_color.x, water_color.y, water_color.z, 0.7)
                    texcoord.addData2(LVector2f(0, 0))  # Dummy UVs
                    block_id_writer.addData3(x, height, z)  # Use local coords for block_id
                
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
