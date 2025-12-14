from ursina import Entity, load_model, color, Mesh, Vec3, Vec2
from util.logger import get_logger, time_block, log_metric
from engine.biomes import BiomeRegistry
from engine.blocks import BlockRegistry


class World:
    CHUNK_SIZE = 16

    def __init__(self, chunk_load_radius=3, chunk_unload_radius=5, max_chunks_per_frame=1, view_distance=4):
        """Initialize the world with dynamic chunk loading parameters.
        
        Args:
            chunk_load_radius: Load chunks within this radius of player (in chunks)
            chunk_unload_radius: Unload chunks beyond this radius of player (in chunks)
            max_chunks_per_frame: Maximum chunks to generate per frame (prevents stuttering)
            view_distance: Maximum render distance in chunks
        """
        self.chunks = {}
        self.logger = get_logger("world")
        
        # Dynamic loading parameters
        self.chunk_load_radius = chunk_load_radius
        self.chunk_unload_radius = chunk_unload_radius
        self.max_chunks_per_frame = max_chunks_per_frame
        self.view_distance = view_distance
        
        # Track player position for chunk management
        self.last_player_chunk = None
        
        # Queues for deferred chunk operations
        self.chunks_to_load = []  # List of (chunk_x, chunk_z) tuples
        self.chunks_to_unload = []  # List of (chunk_x, chunk_z) tuples

    def get_height(self, x, z):
        """Return terrain height at world coordinate (x, z).
        
        Uses biome-specific height functions for terrain variety.
        Action-RPG oriented:
        - Ground level at y=0
        - Gentle slopes and broad shapes
        - No deep pits or extreme heights
        - Returns integer for block alignment
        """
        # Determine biome at this location
        biome = BiomeRegistry.get_biome_at(x, z)
        
        # Use biome's height function
        return biome.height_function(x, z)

    def get_player_chunk_coords(self, player_pos):
        """Convert world position to chunk coordinates.
        
        Args:
            player_pos: Tuple or Vec3 of (x, y, z) world position
            
        Returns:
            Tuple of (chunk_x, chunk_z)
        """
        # Handle both tuple and Vec3 inputs
        if hasattr(player_pos, 'x'):
            px, pz = player_pos.x, player_pos.z
        else:
            px, pz = player_pos[0], player_pos[2]
            
        chunk_x = int(px // self.CHUNK_SIZE)
        chunk_z = int(pz // self.CHUNK_SIZE)
        return (chunk_x, chunk_z)

    def create_chunk(self, chunk_x, chunk_z):
        """Create a single chunk at chunk coordinates (chunk_x, chunk_z) as a single mesh.

        Uses greedy meshing for top faces and non-greedy side faces where neighbor
        columns are lower. Biome determines height and block types.
        """
        base_x = chunk_x * self.CHUNK_SIZE
        base_z = chunk_z * self.CHUNK_SIZE

        # Precompute height map and biome map for this chunk (local indices)
        heights = [[0 for _ in range(self.CHUNK_SIZE)] for _ in range(self.CHUNK_SIZE)]
        biomes = [[None for _ in range(self.CHUNK_SIZE)] for _ in range(self.CHUNK_SIZE)]
        
        for x in range(self.CHUNK_SIZE):
            for z in range(self.CHUNK_SIZE):
                world_x = base_x + x
                world_z = base_z + z
                heights[x][z] = self.get_height(world_x, world_z)
                biomes[x][z] = BiomeRegistry.get_biome_at(world_x, world_z)

        vertices = []
        triangles = []
        uvs = []
        index = 0

        # --- Greedy meshing for top faces ---
        visited = [[False for _ in range(self.CHUNK_SIZE)] for _ in range(self.CHUNK_SIZE)]

        for z in range(self.CHUNK_SIZE):
            for x in range(self.CHUNK_SIZE):
                if visited[x][z]:
                    continue

                h = heights[x][z]

                # Skip if this column is below some cutoff? For now, always render top.

                # Determine width in +X direction
                width = 1
                while x + width < self.CHUNK_SIZE and not visited[x + width][z] \
                        and heights[x + width][z] == h:
                    width += 1

                # Determine height in +Z direction
                height_z = 1
                expanding = True
                while z + height_z < self.CHUNK_SIZE and expanding:
                    for dx in range(width):
                        if visited[x + dx][z + height_z] or heights[x + dx][z + height_z] != h:
                            expanding = False
                            break
                    if expanding:
                        height_z += 1

                # Mark visited
                for dz in range(height_z):
                    for dx in range(width):
                        visited[x + dx][z + dz] = True

                # World-space rectangle
                wx0 = base_x + x
                wx1 = base_x + x + width
                wz0 = base_z + z
                wz1 = base_z + z + height_z
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
                uvs.extend([
                    Vec2(0, 0),
                    Vec2(1, 0),
                    Vec2(1, 1),
                    Vec2(0, 1),
                ])
                index += 4

        # --- Side faces (non-greedy), using height map ---
        for x in range(self.CHUNK_SIZE):
            for z in range(self.CHUNK_SIZE):
                h = heights[x][z]
                world_x = base_x + x
                world_z = base_z + z

                # Neighbor heights (use height map inside chunk, get_height just outside)
                if x + 1 < self.CHUNK_SIZE:
                    h_east = heights[x + 1][z]
                else:
                    h_east = self.get_height(world_x + 1, world_z)

                if x - 1 >= 0:
                    h_west = heights[x - 1][z]
                else:
                    h_west = self.get_height(world_x - 1, world_z)

                if z + 1 < self.CHUNK_SIZE:
                    h_south = heights[x][z + 1]
                else:
                    h_south = self.get_height(world_x, world_z + 1)

                if z - 1 >= 0:
                    h_north = heights[x][z - 1]
                else:
                    h_north = self.get_height(world_x, world_z - 1)

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
                        triangles.extend([
                            index, index + 1, index + 2,
                            index, index + 2, index + 3,
                        ])
                        uvs.extend([
                            Vec2(0, 0),
                            Vec2(1, 0),
                            Vec2(1, 1),
                            Vec2(0, 1),
                        ])
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
                        triangles.extend([
                            index, index + 1, index + 2,
                            index, index + 2, index + 3,
                        ])
                        uvs.extend([
                            Vec2(0, 0),
                            Vec2(1, 0),
                            Vec2(1, 1),
                            Vec2(0, 1),
                        ])
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
                        triangles.extend([
                            index, index + 1, index + 2,
                            index, index + 2, index + 3,
                        ])
                        uvs.extend([
                            Vec2(0, 0),
                            Vec2(1, 0),
                            Vec2(1, 1),
                            Vec2(0, 1),
                        ])
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
                        triangles.extend([
                            index, index + 1, index + 2,
                            index, index + 2, index + 3,
                        ])
                        uvs.extend([
                            Vec2(0, 0),
                            Vec2(1, 0),
                            Vec2(1, 1),
                            Vec2(0, 1),
                        ])
                        index += 4

        # Create mesh for this chunk
        mesh = Mesh(vertices=vertices, triangles=triangles, uvs=uvs, mode='triangle')

        # Determine dominant biome for this chunk (use center)
        center_x = self.CHUNK_SIZE // 2
        center_z = self.CHUNK_SIZE // 2
        dominant_biome = biomes[center_x][center_z]
        
        # Get block color from biome's surface block
        surface_block = BlockRegistry.get_block(dominant_biome.surface_block)
        
        # Parent entity for this chunk (single renderable + collider)
        # Use colored blocks instead of texture for rapid prototyping
        chunk_entity = Entity(
            model=mesh,
            color=color.rgb(*surface_block.color),  # Colored blocks
            collider='mesh'
        )
        self.chunks[(chunk_x, chunk_z)] = chunk_entity

        # Log simple mesh stats for baseline metrics
        vertex_count = len(vertices)
        triangle_count = len(triangles) // 3
        log_metric(
            "chunk_mesh_triangles",
            float(triangle_count),
            labels={"chunk_x": chunk_x, "chunk_z": chunk_z, "vertices": vertex_count},
        )

    def update(self, player_pos):
        """Update chunk loading/unloading based on player position.
        
        Should be called each frame from the game loop.
        
        Args:
            player_pos: Current player position (tuple or Vec3)
        """
        # Get player's current chunk coordinates
        player_chunk = self.get_player_chunk_coords(player_pos)
        
        # Check if player moved to a new chunk
        if self.last_player_chunk != player_chunk:
            self.last_player_chunk = player_chunk
            self._update_chunk_queues(player_chunk)
        
        # Process loading queue (limited per frame to prevent stuttering)
        self._process_loading_queue()
        
        # Process unloading queue (limited per frame)
        self._process_unloading_queue()
    
    def _update_chunk_queues(self, player_chunk):
        """Update the loading and unloading queues based on player chunk position.
        
        Args:
            player_chunk: Tuple of (chunk_x, chunk_z) where player currently is
        """
        player_cx, player_cz = player_chunk
        
        # Find chunks that should be loaded
        chunks_to_load = set()
        for cx in range(player_cx - self.chunk_load_radius, player_cx + self.chunk_load_radius + 1):
            for cz in range(player_cz - self.chunk_load_radius, player_cz + self.chunk_load_radius + 1):
                # Check if within circular radius (not just square)
                dx = cx - player_cx
                dz = cz - player_cz
                distance = (dx * dx + dz * dz) ** 0.5
                
                if distance <= self.chunk_load_radius and (cx, cz) not in self.chunks:
                    chunks_to_load.add((cx, cz))
        
        # Find chunks that should be unloaded
        chunks_to_unload = set()
        for chunk_coords in self.chunks.keys():
            cx, cz = chunk_coords
            dx = cx - player_cx
            dz = cz - player_cz
            distance = (dx * dx + dz * dz) ** 0.5
            
            if distance > self.chunk_unload_radius:
                chunks_to_unload.add(chunk_coords)
        
        # Sort by distance (closest first for loading, farthest first for unloading)
        def distance_to_player(chunk_coords):
            cx, cz = chunk_coords
            return (cx - player_cx) ** 2 + (cz - player_cz) ** 2
        
        self.chunks_to_load = sorted(chunks_to_load, key=distance_to_player)
        self.chunks_to_unload = sorted(chunks_to_unload, key=distance_to_player, reverse=True)
        
        # Log chunk management activity
        if chunks_to_load or chunks_to_unload:
            self.logger.debug(
                f"Chunk update: {len(chunks_to_load)} to load, "
                f"{len(chunks_to_unload)} to unload at player chunk {player_chunk}"
            )
    
    def _process_loading_queue(self):
        """Process chunk loading queue, generating up to max_chunks_per_frame."""
        chunks_loaded = 0
        while self.chunks_to_load and chunks_loaded < self.max_chunks_per_frame:
            chunk_coords = self.chunks_to_load.pop(0)
            cx, cz = chunk_coords
            
            # Double-check it's not already loaded (could happen if player moves fast)
            if chunk_coords not in self.chunks:
                with time_block("chunk_create", self.logger, {"chunk_x": cx, "chunk_z": cz}):
                    self.create_chunk(cx, cz)
                chunks_loaded += 1
                
                log_metric("chunks_loaded", 1.0, labels={"total_chunks": len(self.chunks)})
    
    def _process_unloading_queue(self):
        """Process chunk unloading queue, removing up to max_chunks_per_frame."""
        chunks_unloaded = 0
        while self.chunks_to_unload and chunks_unloaded < self.max_chunks_per_frame:
            chunk_coords = self.chunks_to_unload.pop(0)
            
            # Double-check it still exists
            if chunk_coords in self.chunks:
                chunk_entity = self.chunks[chunk_coords]
                
                # Destroy the entity (frees up memory and rendering)
                from ursina import destroy
                destroy(chunk_entity)
                
                del self.chunks[chunk_coords]
                chunks_unloaded += 1
                
                log_metric("chunks_unloaded", 1.0, labels={"total_chunks": len(self.chunks)})
    
    def set_chunk_visibility(self, camera, player_pos):
        """Update chunk visibility based on camera frustum and view distance.
        
        Should be called each frame after update().
        
        Args:
            camera: The Ursina camera object
            player_pos: Current player position for distance calculations
        """
        player_chunk = self.get_player_chunk_coords(player_pos)
        player_cx, player_cz = player_chunk
        
        for chunk_coords, chunk_entity in self.chunks.items():
            cx, cz = chunk_coords
            
            # Calculate distance from player chunk
            dx = cx - player_cx
            dz = cz - player_cz
            distance = (dx * dx + dz * dz) ** 0.5
            
            # Disable chunks beyond view distance
            if distance > self.view_distance:
                chunk_entity.enabled = False
                continue
            
            # Simple frustum culling: disable chunks behind player
            # Get chunk center in world coordinates
            chunk_center_x = (cx + 0.5) * self.CHUNK_SIZE
            chunk_center_z = (cz + 0.5) * self.CHUNK_SIZE
            
            # Vector from camera to chunk
            if hasattr(player_pos, 'x'):
                cam_x, cam_z = player_pos.x, player_pos.z
            else:
                cam_x, cam_z = player_pos[0], player_pos[2]
            
            to_chunk_x = chunk_center_x - cam_x
            to_chunk_z = chunk_center_z - cam_z
            
            # Camera forward direction (use player's forward since camera follows player)
            from ursina import Vec3
            cam_forward = camera.forward
            
            # Dot product to check if chunk is in front of camera
            # If negative, chunk is behind camera
            dot = to_chunk_x * cam_forward.x + to_chunk_z * cam_forward.z
            
            if dot < -self.CHUNK_SIZE:  # Give some buffer for chunks slightly behind
                chunk_entity.enabled = False
            else:
                chunk_entity.enabled = True