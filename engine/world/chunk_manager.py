"""
Chunk streaming and management system.

Handles distance-based loading/unloading, collision generation, 
water handling, and mesh creation for voxel worlds.
"""

from typing import Dict, Tuple, Optional, Any
from panda3d.core import (
    NodePath, CollisionNode, CollisionPolygon, LVector3f,
    BitMask32, TransparencyAttrib, BoundingSphere, Point3
)

from engine.ecs.system import System
from engine.rendering.mesh import MeshBuilder


class ChunkManager(System):
    """Generic chunk streaming manager for voxel worlds.
    
    Handles:
    - Distance-based chunk loading/unloading around player
    - Collision geometry generation from voxel grids
    - Water block insertion for heights below sea level
    - Mesh creation via MeshBuilder
    
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
        
        # Track last player chunk to optimize updates
        self.last_player_chunk: Optional[Tuple[int, int]] = None
        
        # Water animation time
        self.water_time: float = 0.0
        
        # Frustum culling settings
        # Chunks within this radius (in chunks) are ALWAYS visible to prevent spawn issues
        self.frustum_culling_min_radius: int = 2
    
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
    
    def create_chunk(self, chunk_x: int, chunk_z: int) -> NodePath:
        """Generate and attach a chunk to the scene.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            
        Returns:
            NodePath containing chunk mesh and collision
        """
        # 1. Generate voxel grid from game-specific generator
        voxel_grid = self.generator.generate_chunk(chunk_x, chunk_z, self.chunk_size)
        
        # 2. Add water blocks below sea level
        self._add_water_to_grid(voxel_grid, chunk_x, chunk_z)
        
        # 3. Separate water blocks from solid blocks
        water_blocks = []
        solid_grid = {}
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
        
        # 9. Add collision geometry
        self._add_collision_to_chunk(chunk_np, solid_grid, chunk_x, chunk_z)
        
        # 10. Store reference
        self.chunks[(chunk_x, chunk_z)] = chunk_np
        
        return chunk_np
    
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
        
        Args:
            chunk_np: NodePath to attach collision to
            voxel_grid: Voxel grid with block data
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
        """
        block_registry = self.generator.get_block_registry()
        
        cnode = CollisionNode(f'chunk_collision_{chunk_x}_{chunk_z}')
        cnode.setFromCollideMask(BitMask32.bit(1))
        cnode.setIntoCollideMask(BitMask32.bit(1))
        
        base_x = chunk_x * self.chunk_size
        base_z = chunk_z * self.chunk_size
        
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
            world_x = base_x + x
            world_z = base_z + z
            
            # Check each face for exposure
            for dx, dy, dz, face in directions:
                neighbor = (x + dx, y + dy, z + dz)
                
                # Face is exposed if neighbor is empty or non-solid
                exposed = True
                if neighbor in voxel_grid:
                    neighbor_name = voxel_grid[neighbor]
                    try:
                        neighbor_def = block_registry.get_block(neighbor_name)
                        if neighbor_def.solid:
                            exposed = False
                    except KeyError:
                        pass
                
                if exposed:
                    # Create collision quad for this face
                    self._add_collision_face(cnode, world_x, y, world_z, face)
        
        chunk_np.attachNewNode(cnode)
    
    def _add_collision_face(
        self,
        cnode: CollisionNode,
        world_x: int,
        y: int,
        world_z: int,
        face: str
    ):
        """Add a collision quad for a block face.
        
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
        for chunk_pos, _ in chunks_to_load:
            if chunks_loaded >= self.max_chunks_per_frame:
                break
            self.create_chunk(chunk_pos[0], chunk_pos[1])
            chunks_loaded += 1
        
        # Unload distant chunks
        chunks_to_unload = []
        for chunk_pos in list(self.chunks.keys()):
            dx = chunk_pos[0] - player_chunk_x
            dz = chunk_pos[1] - player_chunk_z
            distance_sq = dx * dx + dz * dz
            
            if distance_sq > self.unload_radius * self.unload_radius:
                chunks_to_unload.append(chunk_pos)
        
        for chunk_pos in chunks_to_unload:
            self.unload_chunk(chunk_pos[0], chunk_pos[1])
