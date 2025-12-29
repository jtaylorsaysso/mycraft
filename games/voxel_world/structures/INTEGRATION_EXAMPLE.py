"""Example integration of structure generation with chunk creation.

This shows how the structure generator would be called during world generation.
This is NOT the final implementation - just a demonstration of the workflow.
"""

# EXAMPLE INTEGRATION (conceptual):
# In TerrainSystem.create_chunk(), after generating heightmap:

def create_chunk_with_structures(self, chunk_x: int, chunk_z: int):
    """Generate chunk with terrain AND structures."""
    
    # 1. Generate heightmap and biome data (existing code)
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
    
    # 2. Create voxel grid for chunk (3D array of block types)
    # This replaces the direct mesh building with a data structure
    # that can be modified before meshing
    voxel_grid = self._create_voxel_grid(heights, biomes)
    
    # 3. Generate structures and add to voxel grid
    self._add_structures_to_grid(voxel_grid, chunk_x, chunk_z, biomes, heights)
    
    # 4. Build mesh from voxel grid (existing greedy meshing logic)
    geom_node = MeshBuilder.build_chunk_mesh_from_grid(
        voxel_grid, chunk_x, chunk_z, self.chunk_size, self.texture_atlas
    )
    
    # 5. Continue with water, collision, etc. (existing code)
    # ...

def _create_voxel_grid(self, heights, biomes):
    """Create 3D grid of block types from heightmap.
    
    Returns:
        3D array: voxel_grid[x][y][z] = block_name or None
    """
    grid = {}  # Use dict for sparse storage: (x, y, z) -> block_name
    
    for x in range(self.chunk_size):
        for z in range(self.chunk_size):
            h = heights[x][z]
            biome = biomes[x][z]
            
            # Place terrain blocks
            for y in range(h + 1):
                if y == h:
                    block_name = biome.surface_block
                else:
                    block_name = biome.subsurface_block
                
                grid[(x, y, z)] = block_name
    
    return grid

def _add_structures_to_grid(self, voxel_grid, chunk_x, chunk_z, biomes, heights):
    """Add structures (trees, etc.) to the voxel grid.
    
    Args:
        voxel_grid: Dict mapping (x, y, z) -> block_name
        chunk_x, chunk_z: Chunk coordinates
        biomes: 2D array of biomes per block
        heights: 2D array of terrain heights
    """
    from games.voxel_world.structures import TreeGenerator
    
    # Example: Add trees to forest biome
    for x in range(self.chunk_size):
        for z in range(self.chunk_size):
            biome = biomes[x][z]
            
            if biome.name == "forest":
                # Use tree generator
                tree_gen = TreeGenerator(seed=self.world_seed, tree_type="standard")
                
                world_x = chunk_x * self.chunk_size + x
                world_z = chunk_z * self.chunk_size + z
                
                # Check if tree should spawn here (noise-based)
                if tree_gen.should_generate_at(world_x, world_z, density=0.08, scale=0.3):
                    h = heights[x][z]
                    
                    # Generate tree structure
                    structure = tree_gen.generate_structure(
                        world_x, h, world_z, 
                        height_callback=self.get_height
                    )
                    
                    if structure:
                        # Add tree blocks to grid
                        for block_x, block_y, block_z, block_name in structure.blocks:
                            # Convert world coords to chunk-local coords
                            local_x = block_x - (chunk_x * self.chunk_size)
                            local_z = block_z - (chunk_z * self.chunk_size)
                            
                            # Only add if within this chunk's bounds
                            if 0 <= local_x < self.chunk_size and 0 <= local_z < self.chunk_size:
                                voxel_grid[(local_x, block_y, local_z)] = block_name
            
            elif biome.name == "swamp":
                # Dead trees in swamps
                tree_gen = TreeGenerator(seed=self.world_seed, tree_type="dead")
                # ... similar logic with lower density
            
            # Add other structure types per biome...
