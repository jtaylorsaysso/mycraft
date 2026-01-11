"""
Chunk streaming and management system.

Handles distance-based loading/unloading, collision generation, 
water handling, and mesh creation for voxel worlds.
"""

# TODO: Refactor this; getting untidy

from typing import Dict, Tuple, Optional, Any
from panda3d.core import (
    NodePath, CollisionNode, CollisionPolygon, LVector3f,
    BitMask32, TransparencyAttrib, BoundingSphere, Point3
)

from engine.ecs.system import System
from engine.rendering.mesh import MeshBuilder
# Import trimesh utilities safely
try:
    from engine.rendering import (
        trimesh_available,
        voxel_to_trimesh
    )
except ImportError:
    # Fallback if imports fail (though rendering.__init__ should handle this)
    trimesh_available = lambda: False
    voxel_to_trimesh = lambda grid: None


class ChunkManager(System):
    """Generic chunk streaming manager for voxel worlds.
    
    Handles:
    - Distance-based chunk loading/unloading around player
    - Collision geometry generation from voxel grids
    - Water block insertion for heights below sea level
    - Mesh creation via MeshBuilder
    - [NEW] Trimesh caching for physics queries
    
    Games provide a ChunkGenerator implementation that defines
    how terrain is generated; ChunkManager handles the rest.
    """
    
    def __init__(
        self, 
        world: Any,
        event_bus: Any,
        base: Any,
        generator: Any,  # ChunkGenerator protocol
        texture_atlas: Optional[Any] = None,
        chunk_size: int = 16,
        load_radius: int = 6,
        unload_radius: int = 8,
        max_chunks_per_frame: int = 3,
        sea_level: int = 0,
        complex_water: bool = False
    ):
        """Initialize chunk manager.
        
        Args:
            world: ECS World instance
            event_bus: Event bus for world events
            base: Panda3D ShowBase instance
            generator: ChunkGenerator implementation
            texture_atlas: Optional TextureAtlas for block textures
            chunk_size: Size of chunks in blocks (default 16)
            load_radius: Load chunks within this radius (in chunks)
            unload_radius: Unload chunks beyond this radius (in chunks)
            max_chunks_per_frame: Throttle chunk loading per frame
            sea_level: Y level for water generation (blocks below get water)
            complex_water: If True, uses shaders and physics for water. If False, renders as simple blocks.
        """
        super().__init__(world, event_bus)
        
        self.base = base
        self.generator = generator
        self.texture_atlas = texture_atlas
        self.chunk_size = chunk_size
        self.load_radius = load_radius
        self.unload_radius = unload_radius
        self.max_chunks_per_frame = max_chunks_per_frame
        self.sea_level = sea_level
        self.complex_water = complex_water
        
        # Loaded chunks: (chunk_x, chunk_z) -> NodePath
        self.chunks: Dict[Tuple[int, int], NodePath] = {}
        
        # Track water meshes separately for animation
        self.water_nodes: Dict[Tuple[int, int], NodePath] = {}
        
        # [NEW] Check for trimesh availability once
        self.has_trimesh = trimesh_available()
        # [NEW] Cache trimesh objects for physics queries: (chunk_x, chunk_z) -> trimesh.Trimesh
        self.chunk_meshes: Dict[Tuple[int, int], Any] = {}
        
        # Track last player chunk to optimize updates
        self.last_player_chunk: Optional[Tuple[int, int]] = None
        
        # Water animation time
        self.water_time: float = 0.0
        
        # Frustum culling settings
        # Chunks within this radius (in chunks) are ALWAYS visible to prevent spawn issues
        self.frustum_culling_min_radius: int = 2
        
        # Store voxel grids for cross-chunk collision checks
        self.voxel_grids: Dict[Tuple[int, int], Dict[Tuple[int, int, int], str]] = {}
        
        # Debug tracking
        self.debug_enabled = True
        self.frame_count = 0
        self.last_debug_time = 0.0
        self.chunk_create_times = []  # Track chunk creation times
        self.total_time = 0.0
    
    def get_height(self, x: float, z: float) -> float:
        """Get terrain height at world position.
        
        Delegates to the generator.
        
        Args:
            x: World X coordinate
            z: World Z coordinate
            
        Returns:
            Height at this position
        """
        return self.generator.get_height(x, z)
        
    def get_terrain_mesh(self) -> Optional[Any]:
        """Get a combined trimesh of all loaded chunks.
        
        Useful for batch ray queries or analysis.
        
        Returns:
            Combined trimesh.Trimesh object or None if trimesh not available/no chunks.
        """
        if not self.has_trimesh or not self.chunk_meshes:
            return None
            
        import trimesh
        # Efficiently concatenate all cached meshes
        # Note: This creates a new mesh copy, so don't call every frame!
        try:
            return trimesh.util.concatenate(list(self.chunk_meshes.values()))
        except Exception as e:
            print(f"Error concatenating meshes: {e}")
            return None
    
    def create_chunk(self, chunk_x: int, chunk_z: int) -> NodePath:
        """Generate and attach a chunk to the scene.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            
        Returns:
            NodePath containing chunk mesh and collision
        """
        import time
        start_time = time.time()
        # 1. Generate voxel grid, entities, and chest loot from game-specific generator
        voxel_grid, entities, chest_loot = self.generator.generate_chunk(chunk_x, chunk_z, self.chunk_size)
        
        # 1b. Spawn entities
        if entities:
            # Lazy import to avoid circular dependency
            from games.voxel_world.entity.factory import EntityFactory
            
            for entity_tuple in entities:
                # Check if tuple has color
                if len(entity_tuple) == 5:
                    entity_type, ex, ey, ez, color_name = entity_tuple
                else:
                    entity_type, ex, ey, ez = entity_tuple
                    color_name = None

                # Use chunk coordinates to create a stable seed for the entity
                entity_seed = hash((ex, ey, ez))
                
                EntityFactory.create_enemy(
                    self.world, 
                    entity_type, 
                    (float(ex), float(ey), float(ez)), 
                    entity_seed,
                    color_name=color_name
                )
        
        # 1c. Spawn chest entities
        if chest_loot:
            # Lazy import to avoid circular dependency
            from engine.components.chest import ChestComponent
            from engine.components.core import Transform
            from panda3d.core import LVector3f
            
            for chest_pos, items in chest_loot.items():
                # Create chest entity
                chest_entity = self.world.create_entity()
                
                # Add Transform at chest block position (center of block)
                cx, cy, cz = chest_pos
                self.world.add_component(
                    chest_entity,
                    Transform(position=LVector3f(float(cx) + 0.5, float(cy) + 0.5, float(cz) + 0.5))
                )
                
                # Add ChestComponent with loot data
                self.world.add_component(
                    chest_entity,
                    ChestComponent(
                        position=chest_pos,
                        items=items,
                        is_open=False,
                        poi_type="poi"  # Could be enhanced to track specific POI type
                    )
                )
        
        # 2. Add water blocks below sea level
        self._add_water_to_grid(voxel_grid, chunk_x, chunk_z)
        
        # 3. Separate water blocks from solid blocks
        water_blocks = []
        solid_grid = {}
        for pos, block_name in voxel_grid.items():
            if block_name == "water" and self.complex_water:
                water_blocks.append(pos)
            else:
                # If complex water is off, treat water as a normal solid block (it will use fallback color/texture)
                solid_grid[pos] = block_name
        
        # 4. Build solid terrain mesh
        block_registry = self.generator.get_block_registry()
        geom_node = MeshBuilder.build_chunk_mesh_from_grid(
            solid_grid, 
            chunk_x, 
            chunk_z, 
            self.chunk_size,
            self.texture_atlas,
            block_registry
        )
        
        # 5. Create NodePath and attach to scene
        chunk_np = self.base.render.attachNewNode(geom_node)
        
        # 5b. Position chunk at world coordinates
        # Since mesh and collision use local coordinates (0 to chunk_size),
        # we position the chunk NodePath at the chunk's world position
        world_x = chunk_x * self.chunk_size
        world_z = chunk_z * self.chunk_size
        chunk_np.setPos(world_x, world_z, 0)
        
        # 6. Apply texture if available
        if self.texture_atlas and self.texture_atlas.is_loaded():
            chunk_np.setTexture(self.texture_atlas.get_texture())
            chunk_np.setTransparency(TransparencyAttrib.MAlpha)
        
        # 7. Build and attach water mesh with wobble shader
        if water_blocks:
            from engine.rendering.shaders import WATER_WOBBLE_SHADER
            
            water_geom = MeshBuilder.build_water_mesh(
                water_blocks,
                chunk_x,
                chunk_z,
                self.chunk_size
            )
            
            if water_geom:
                water_np = chunk_np.attachNewNode(water_geom)
                water_np.setShader(WATER_WOBBLE_SHADER)
                water_np.setShaderInput("time", self.water_time)
                water_np.setShaderInput("wobble_frequency", 2.0)
                water_np.setShaderInput("wobble_amplitude", 0.08)
                water_np.setShaderInput("water_alpha", 0.7)
                water_np.setTransparency(TransparencyAttrib.MAlpha)
                water_np.setBin("transparent", 0)
                water_np.setDepthWrite(False)
                
                # Track for animation updates
                self.water_nodes[(chunk_x, chunk_z)] = water_np
            
            # 8. Register water blocks with physics system
            from engine.systems.water_physics import WaterPhysicsSystem
            water_system = self.world.get_system_by_type("WaterPhysicsSystem")
            if water_system:
                base_x = chunk_x * self.chunk_size
                base_z = chunk_z * self.chunk_size
                for (x, y, z) in water_blocks:
                    world_x = base_x + x
                    world_z = base_z + z
                    water_system.register_water_block(world_x, y, world_z)
        
        # 9. Store voxel grid for cross-chunk collision checks
        self.voxel_grids[(chunk_x, chunk_z)] = solid_grid
        
        # 10. Add collision geometry
        self._add_collision_to_chunk(chunk_np, solid_grid, chunk_x, chunk_z)
        
        # [NEW] 10b. Generate and cache trimesh for this chunk
        if self.has_trimesh:
            try:
                # Convert the solid grid to a trimesh object
                mesh = voxel_to_trimesh(solid_grid)
                if not mesh.is_empty:
                    # Translate mesh to world coordinates
                    # voxel_to_trimesh creates mesh at local 0,0,0
                    # We need to shift it by world_x, world_z
                    # Note: Y is up in Trimesh usually, but here Y and Z might be swapped?
                    # In voxel_to_trimesh: vertices are (x, y, z) where y is height.
                    # In Panda3D world: (x, depth_y, height_z).
                    # Actually, in `_add_collision_face`:
                    # v0 = LVector3f(world_x, world_z, y + 1) -> X, Y(depth), Z(height)
                    # So Y in voxel grid (height) maps to Z in Panda3D.
                    # Z in voxel grid (depth) maps to Y in Panda3D.
                    
                    # Our voxel_to_trimesh implementation in trimesh_utils.py just creates boxes at (x, y, z).
                    # If we want to use this for raycasting in Panda3D space, we need to transform it.
                    # OR we just cache it as-is (local voxel coords) and handle transform later.
                    # But `voxel_to_trimesh` likely produces a mesh where coordinates match the keys.
                    # So a voxel at (0, 5, 0) becomes a box at (0, 5, 0).
                    # But in Panda3D world, that should be at (ChunkWorldX + 0, ChunkWorldZ + 0, 5).
                    
                    # Let's transform it to World Space for easier batch raycasting later.
                    # Transform matrix: 
                    # X_mesh -> X_world
                    # Y_mesh (height) -> Z_world (height)
                    # Z_mesh (depth) -> Y_world (depth)
                    
                    # Wait, trimesh uses XYZ.
                    chunk_world_x = chunk_x * self.chunk_size
                    chunk_world_z = chunk_z * self.chunk_size
                    
                    # Create transform matrix
                    import numpy as np
                    transform = np.eye(4)
                    
                    # Rotation/Permutation to swap Y and Z?
                    # Voxel (x, y=height, z=depth) -> World (x, depth, height)
                    # So:
                    # New X = Old X + WorldX
                    # New Y = Old Z + WorldZ
                    # New Z = Old Y
                    
                    # Actually, looking at `mesh_numpy.generate_smooth_terrain_mesh`:
                    # we did `vertices_xzy = np.column_stack([x, z, y])`
                    # We should probably do similar here if we want the cached mesh to match world space.
                    # HOWEVER, trimesh objects are usually manipulated with 4x4 matrices.
                    
                    # Let's simple apply a translation to correct X and Z (depth), 
                    # and swap Y/Z axes.
                    
                    # Step 1: Swap Y and Z to match Panda3D (up=Z)
                    # This changes (x, y, z) to (x, z, y)
                    permut = np.array([
                        [1, 0, 0, 0],
                        [0, 0, 1, 0],
                        [0, 1, 0, 0],
                        [0, 0, 0, 1]
                    ])
                    mesh.apply_transform(permut)
                    
                    # Step 2: Translate to world position
                    # Now mesh is (x, depth, height)
                    trans = np.eye(4)
                    trans[0, 3] = chunk_world_x
                    trans[1, 3] = chunk_world_z
                    mesh.apply_transform(trans)
                    
                    self.chunk_meshes[(chunk_x, chunk_z)] = mesh
            except Exception as e:
                print(f"Failed to generate trimesh for chunk ({chunk_x}, {chunk_z}): {e}")
        
        # 11. Store reference
        self.chunks[(chunk_x, chunk_z)] = chunk_np
        
        # Debug: Track chunk creation time
        if self.debug_enabled:
            elapsed = time.time() - start_time
            self.chunk_create_times.append(elapsed)
            if elapsed > 0.016:  # More than one frame at 60fps
                print(f"⚠️ Chunk ({chunk_x}, {chunk_z}) took {elapsed*1000:.1f}ms to create")
        
        return chunk_np
    
    def _is_neighbor_solid(
        self,
        x: int, y: int, z: int,
        chunk_x: int, chunk_z: int,
        voxel_grid: Dict[Tuple[int, int, int], str]
    ) -> bool:
        """Check if a neighbor block is solid, including cross-chunk neighbors.
        
        Args:
            x, y, z: Local coordinates within current chunk (may be outside 0-chunk_size range)
            chunk_x, chunk_z: Current chunk coordinates
            voxel_grid: Current chunk's voxel grid
            
        Returns:
            True if neighbor is solid, False otherwise
        """
        # Check if neighbor is within current chunk
        if 0 <= x < self.chunk_size and 0 <= z < self.chunk_size:
            if (x, y, z) in voxel_grid:
                neighbor_name = voxel_grid[(x, y, z)]
                try:
                    block_def = self.generator.get_block_registry().get_block(neighbor_name)
                    return block_def.solid
                except KeyError:
                    return False
            return False
        
        # Neighbor is in adjacent chunk - calculate which chunk
        neighbor_chunk_x = chunk_x
        neighbor_chunk_z = chunk_z
        local_x = x
        local_z = z
        
        # Adjust chunk coordinates if neighbor crosses boundary
        if x < 0:
            neighbor_chunk_x -= 1
            local_x = self.chunk_size + x  # x is negative, so this wraps around
        elif x >= self.chunk_size:
            neighbor_chunk_x += 1
            local_x = x - self.chunk_size
            
        if z < 0:
            neighbor_chunk_z -= 1
            local_z = self.chunk_size + z  # z is negative, so this wraps around
        elif z >= self.chunk_size:
            neighbor_chunk_z += 1
            local_z = z - self.chunk_size
        
        # Look up neighboring chunk's voxel grid
        neighbor_chunk_key = (neighbor_chunk_x, neighbor_chunk_z)
        if neighbor_chunk_key not in self.voxel_grids:
            # Chunk not loaded yet - assume not solid (will be corrected when chunk loads)
            return False
        
        neighbor_grid = self.voxel_grids[neighbor_chunk_key]
        if (local_x, y, local_z) not in neighbor_grid:
            return False
        
        neighbor_name = neighbor_grid[(local_x, y, local_z)]
        try:
            block_def = self.generator.get_block_registry().get_block(neighbor_name)
            return block_def.solid
        except KeyError:
            return False
    
    def _add_water_to_grid(
        self, 
        voxel_grid: Dict[Tuple[int, int, int], str],
        chunk_x: int,
        chunk_z: int
    ):
        """Insert water blocks for heights below sea level.
        
        Args:
            voxel_grid: Voxel grid to modify in-place
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
        """
        # if self.sea_level <= 0 check removed to allow water at y<0

            
        for x in range(self.chunk_size):
            for z in range(self.chunk_size):
                # Find highest solid block at this column
                max_y = None
                for (bx, by, bz), block_name in voxel_grid.items():
                    if bx == x and bz == z:
                        if max_y is None or by > max_y:
                            max_y = by
                
                if max_y is None:
                    max_y = -10  # Default if no blocks
                
                # Add water above terrain up to sea level
                if max_y < self.sea_level:
                    for y in range(max_y + 1, self.sea_level):
                        if (x, y, z) not in voxel_grid:
                            voxel_grid[(x, y, z)] = "water"
    
    def _add_collision_to_chunk(
        self,
        chunk_np: NodePath,
        voxel_grid: Dict[Tuple[int, int, int], str],
        chunk_x: int,
        chunk_z: int
    ):
        """Add collision geometry for solid blocks.
        
        Creates collision in world coordinates and attaches directly to render.
        This ensures collision detection works properly with the physics system.
        
        Args:
            chunk_np: NodePath for the chunk (for reference)
            voxel_grid: Voxel grid with block data (in local coordinates)
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
        """
        block_registry = self.generator.get_block_registry()
        
        cnode = CollisionNode(f'chunk_collision_{chunk_x}_{chunk_z}')
        cnode.setFromCollideMask(BitMask32.bit(1))
        cnode.setIntoCollideMask(BitMask32.bit(1))
        
        # Calculate world offset for this chunk
        world_x_offset = chunk_x * self.chunk_size
        world_z_offset = chunk_z * self.chunk_size
        
        # Face directions: (dx, dy, dz, name)
        directions = [
            (0, 1, 0, 'top'),
            (0, -1, 0, 'bottom'),
            (1, 0, 0, 'east'),
            (-1, 0, 0, 'west'),
            (0, 0, 1, 'south'),
            (0, 0, -1, 'north')
        ]
        
        for pos, block_name in voxel_grid.items():
            # Skip non-solid blocks
            try:
                block_def = block_registry.get_block(block_name)
            except KeyError:
                continue
                
            if not block_def.solid:
                continue
            
            x, y, z = pos
            # Convert to world coordinates for collision
            world_x = world_x_offset + x
            world_z = world_z_offset + z
            
            # Check each face for exposure
            for dx, dy, dz, face in directions:
                # Skip bottom faces - player never collides from below
                if face == 'bottom':
                    continue
                    
                neighbor_x = x + dx
                neighbor_y = y + dy
                neighbor_z = z + dz
                
                # Check if neighbor is solid (including cross-chunk)
                if self._is_neighbor_solid(neighbor_x, neighbor_y, neighbor_z, chunk_x, chunk_z, voxel_grid):
                    # Neighbor is solid - face is not exposed
                    continue
                
                # Face is exposed - create collision quad
                self._add_collision_face(cnode, world_x, y, world_z, face)
        
        # Attach collision directly to render (not to chunk_np)
        # This ensures collision is in world space
        collision_np = self.base.render.attachNewNode(cnode)
        
        # Store collision node reference for cleanup
        if not hasattr(self, 'collision_nodes'):
            self.collision_nodes = {}
        self.collision_nodes[(chunk_x, chunk_z)] = collision_np
    
    def _add_collision_face(
        self,
        cnode: CollisionNode,
        world_x: int,
        y: int,
        world_z: int,
        face: str
    ):
        """Add a collision quad for a block face.
        
        Uses world coordinates since collision is attached to render.
        
        Args:
            cnode: CollisionNode to add to
            world_x: World X coordinate
            y: Height (Y in voxel space, Z in Panda3D)
            world_z: World Z coordinate (Y in Panda3D)
            face: Face name ('top', 'bottom', 'east', 'west', 'north', 'south')
        """
        if face == 'top':
            v0 = LVector3f(world_x, world_z, y + 1)
            v1 = LVector3f(world_x + 1, world_z, y + 1)
            v2 = LVector3f(world_x + 1, world_z + 1, y + 1)
            v3 = LVector3f(world_x, world_z + 1, y + 1)
        elif face == 'bottom':
            v0 = LVector3f(world_x, world_z + 1, y)
            v1 = LVector3f(world_x + 1, world_z + 1, y)
            v2 = LVector3f(world_x + 1, world_z, y)
            v3 = LVector3f(world_x, world_z, y)
        elif face == 'east':
            v0 = LVector3f(world_x + 1, world_z, y)
            v1 = LVector3f(world_x + 1, world_z + 1, y)
            v2 = LVector3f(world_x + 1, world_z + 1, y + 1)
            v3 = LVector3f(world_x + 1, world_z, y + 1)
        elif face == 'west':
            v0 = LVector3f(world_x, world_z + 1, y)
            v1 = LVector3f(world_x, world_z, y)
            v2 = LVector3f(world_x, world_z, y + 1)
            v3 = LVector3f(world_x, world_z + 1, y + 1)
        elif face == 'south':
            v0 = LVector3f(world_x + 1, world_z + 1, y)
            v1 = LVector3f(world_x, world_z + 1, y)
            v2 = LVector3f(world_x, world_z + 1, y + 1)
            v3 = LVector3f(world_x + 1, world_z + 1, y + 1)
        else:  # north
            v0 = LVector3f(world_x, world_z, y)
            v1 = LVector3f(world_x + 1, world_z, y)
            v2 = LVector3f(world_x + 1, world_z, y + 1)
            v3 = LVector3f(world_x, world_z, y + 1)
        
        # Two triangles per quad
        cnode.addSolid(CollisionPolygon(v0, v1, v2))
        cnode.addSolid(CollisionPolygon(v0, v2, v3))
    
    def _update_frustum_culling(self, player_chunk_x: int, player_chunk_z: int):
        """Update chunk visibility based on camera frustum.
        
        Hides chunks that are outside the camera's view to reduce draw calls.
        Chunks within minimum radius are always visible to prevent spawn issues.
        
        Args:
            player_chunk_x: Player's current chunk X
            player_chunk_z: Player's current chunk Z
        """
        # Get camera node for frustum checking
        if not hasattr(self.base, 'cam') or self.base.cam is None:
            return
            
        cam = self.base.cam
        lens = self.base.camLens
        
        # Create a frustum-based visibility check
        # Use the lens to check if chunk center is in view
        for (cx, cz), chunk_np in self.chunks.items():
            if chunk_np.isEmpty():
                continue
                
            # Distance check: always show chunks within minimum radius
            dx = cx - player_chunk_x
            dz = cz - player_chunk_z
            distance_sq = dx * dx + dz * dz
            
            if distance_sq <= self.frustum_culling_min_radius * self.frustum_culling_min_radius:
                # Always visible when close to player
                if chunk_np.isHidden():
                    chunk_np.show()
                continue
            
            # Calculate chunk center in world coordinates
            # Chunk spans from (cx * chunk_size) to ((cx + 1) * chunk_size)
            center_x = (cx + 0.5) * self.chunk_size
            center_z = (cz + 0.5) * self.chunk_size
            center_y = 0  # Ground level (Z in Panda3D)
            
            # World position (X, Z_depth, Y_height in Panda3D)
            world_pos = Point3(center_x, center_z, center_y)
            
            # Transform to camera-relative coordinates
            try:
                cam_pos = cam.getRelativePoint(self.base.render, world_pos)
            except Exception:
                # If transform fails, keep visible
                if chunk_np.isHidden():
                    chunk_np.show()
                continue
            
            # Check if point is in front of camera (positive Y in camera space)
            # In Panda3D camera space, +Y is forward
            if cam_pos.y <= 0:
                # Behind camera - hide
                if not chunk_np.isHidden():
                    chunk_np.hide()
                continue
            
            # Check if within frustum using lens FOV
            # Use a generous margin to avoid popping
            fov_h = lens.getFov()  # Returns (horizontal, vertical) or single value
            if isinstance(fov_h, tuple):
                fov_margin = fov_h[0] * 0.7  # Use 70% of FOV for margin
            else:
                fov_margin = fov_h * 0.7
            
            # Calculate angle from camera forward to chunk
            import math
            angle_h = math.degrees(math.atan2(abs(cam_pos.x), cam_pos.y))
            
            if angle_h > fov_margin:
                # Outside horizontal FOV - hide
                if not chunk_np.isHidden():
                    chunk_np.hide()
            else:
                # Visible
                if chunk_np.isHidden():
                    chunk_np.show()
    
    def unload_chunk(self, chunk_x: int, chunk_z: int):
        """Remove a chunk from the scene.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
        """
        chunk_key = (chunk_x, chunk_z)
        
        # Remove collision node
        if hasattr(self, 'collision_nodes') and chunk_key in self.collision_nodes:
            self.collision_nodes[chunk_key].removeNode()
            del self.collision_nodes[chunk_key]
        
        # Remove stored voxel grid
        if hasattr(self, 'voxel_grids') and chunk_key in self.voxel_grids:
            del self.voxel_grids[chunk_key]
        
        # [NEW] Remove cached trimesh
        if hasattr(self, 'chunk_meshes') and chunk_key in self.chunk_meshes:
            del self.chunk_meshes[chunk_key]
        
        # Unregister water blocks from physics system
        if chunk_key in self.water_nodes:
            from engine.systems.water_physics import WaterPhysicsSystem
            water_system = self.world.get_system_by_type("WaterPhysicsSystem")
            if water_system:
                base_x = chunk_x * self.chunk_size
                base_z = chunk_z * self.chunk_size
                # Note: We don't track individual water block positions for unloading
                # In a full implementation, we'd track them or iterate the grid again
                # For now, the water system can handle dangling registrations
            
            # Clean up water node
            del self.water_nodes[chunk_key]
        
        # Remove chunk
        if chunk_key in self.chunks:
            self.chunks[chunk_key].removeNode()
            del self.chunks[chunk_key]
    
    def update(self, dt: float):
        """Update chunk streaming based on player position.
        
        Loads nearby chunks and unloads distant ones.
        
        Args:
            dt: Delta time since last update
        """
        import time
        frame_start = time.time()
        
        # Debug: Track frame time and FPS
        self.frame_count += 1
        self.total_time += dt
        
        if self.debug_enabled and self.total_time - self.last_debug_time >= 2.0:
            fps = self.frame_count / (self.total_time - self.last_debug_time)
            avg_chunk_time = sum(self.chunk_create_times) / len(self.chunk_create_times) if self.chunk_create_times else 0
            print(f"📊 FPS: {fps:.1f} | Chunks loaded: {len(self.chunks)} | Avg chunk time: {avg_chunk_time*1000:.1f}ms")
            self.last_debug_time = self.total_time
            self.frame_count = 0
            self.chunk_create_times = []
        # Update water animation time
        self.water_time += dt
        for water_np in self.water_nodes.values():
            if not water_np.isEmpty():
                water_np.setShaderInput("time", self.water_time)
        
        # Get player entity
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            return
        
        from engine.components.core import Transform
        transform = self.world.get_component(player_id, Transform)
        if not transform:
            return
        
        # Calculate player's current chunk
        player_chunk_x = int(transform.position.x // self.chunk_size)
        player_chunk_z = int(transform.position.y // self.chunk_size)  # Y is depth in Panda3D
        player_chunk = (player_chunk_x, player_chunk_z)
        
        # Update frustum culling every frame (for camera rotation)
        self._update_frustum_culling(player_chunk_x, player_chunk_z)
        
        # Skip chunk loading/unloading if player hasn't moved to a new chunk
        if player_chunk == self.last_player_chunk:
            return
        
        self.last_player_chunk = player_chunk
        
        # Determine chunks to load
        chunks_to_load = []
        for dx in range(-self.load_radius, self.load_radius + 1):
            for dz in range(-self.load_radius, self.load_radius + 1):
                # Circular radius check
                distance_sq = dx * dx + dz * dz
                if distance_sq <= self.load_radius * self.load_radius:
                    chunk_pos = (player_chunk_x + dx, player_chunk_z + dz)
                    
                    if chunk_pos not in self.chunks:
                        chunks_to_load.append((chunk_pos, distance_sq))
        
        # Sort by distance (load nearest first)
        chunks_to_load.sort(key=lambda x: x[1])
        
        # Load chunks (throttled)
        chunks_loaded = 0
        if chunks_to_load and self.debug_enabled:
            print(f"🔄 Player moved to chunk {player_chunk}, loading {len(chunks_to_load)} chunks...")
        
        for chunk_pos, _ in chunks_to_load:
            if chunks_loaded >= self.max_chunks_per_frame:
                if self.debug_enabled:
                    print(f"⏸️ Throttled: {len(chunks_to_load) - chunks_loaded} chunks deferred to next frame")
                break
            self.create_chunk(chunk_pos[0], chunk_pos[1])
            chunks_loaded += 1
        
        if chunks_loaded > 0 and self.debug_enabled:
            print(f"✅ Loaded {chunks_loaded} chunks this frame")
        
        # Unload distant chunks
        chunks_to_unload = []
        for chunk_pos in list(self.chunks.keys()):
            dx = chunk_pos[0] - player_chunk_x
            dz = chunk_pos[1] - player_chunk_z
            distance_sq = dx * dx + dz * dz
            
            if distance_sq > self.unload_radius * self.unload_radius:
                chunks_to_unload.append(chunk_pos)
        
        if chunks_to_unload and self.debug_enabled:
            print(f"🗑️ Unloading {len(chunks_to_unload)} distant chunks")
        
        for chunk_pos in chunks_to_unload:
            self.unload_chunk(chunk_pos[0], chunk_pos[1])
        
        # Debug: Track total frame time
        if self.debug_enabled:
            frame_time = time.time() - frame_start
            if frame_time > 0.016:  # More than one frame at 60fps
                print(f"⚠️ ChunkManager.update() took {frame_time*1000:.1f}ms (target: 16ms)")
