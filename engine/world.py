from ursina import Entity, load_model, color, Mesh, Vec3, Vec2
from util.logger import get_logger, time_block, log_metric


class World:
    CHUNK_SIZE = 16
    CHUNK_GRID_RADIUS = 1  # 3x3 chunks centered around origin

    def __init__(self):
        self.chunks = {}
        self.logger = get_logger("world")

        total_chunks = (self.CHUNK_GRID_RADIUS * 2 + 1) ** 2
        with time_block("world_generate", self.logger, {"chunks": total_chunks}):
            self.generate_chunks()

    def get_height(self, x, z):
        """Return terrain height at world coordinate (x, z).
        
        Action-RPG oriented height function:
        - Ground level at y=0
        - Gentle slopes and broad shapes
        - No deep pits or extreme heights
        - Returns integer for block alignment
        """
        import math
        
        # Base ground level
        base_height = 0
        
        # Gentle sine waves for broad, readable terrain
        # Low frequency to avoid noisy terrain
        wave_x = math.sin(x * 0.05) * 2  # ±2 blocks variation
        wave_z = math.cos(z * 0.05) * 2  # ±2 blocks variation
        
        # Combine waves for gentle rolling terrain
        height = base_height + wave_x + wave_z
        
        # Clamp to reasonable range for action-RPG terrain
        # Keep terrain mostly between -2 and +2 relative to ground
        height = max(-2, min(2, height))
        
        # Round to integer for block alignment
        return int(round(height))

    def generate_chunks(self):
        """Generate a 3x3 grid of chunks around the origin."""
        for cx in range(-self.CHUNK_GRID_RADIUS, self.CHUNK_GRID_RADIUS + 1):
            for cz in range(-self.CHUNK_GRID_RADIUS, self.CHUNK_GRID_RADIUS + 1):
                self.create_chunk(cx, cz)

    def create_chunk(self, chunk_x, chunk_z):
        """Create a single chunk at chunk coordinates (chunk_x, chunk_z) as a single mesh.

        Uses greedy meshing for top faces and non-greedy side faces where neighbor
        columns are lower.
        """
        base_x = chunk_x * self.CHUNK_SIZE
        base_z = chunk_z * self.CHUNK_SIZE

        # Precompute height map for this chunk (local indices)
        heights = [[0 for _ in range(self.CHUNK_SIZE)] for _ in range(self.CHUNK_SIZE)]
        for x in range(self.CHUNK_SIZE):
            for z in range(self.CHUNK_SIZE):
                world_x = base_x + x
                world_z = base_z + z
                heights[x][z] = self.get_height(world_x, world_z)

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

        # Parent entity for this chunk (single renderable + collider)
        chunk_entity = Entity(model=mesh, texture='grass', collider='mesh')
        self.chunks[(chunk_x, chunk_z)] = chunk_entity

        # Log simple mesh stats for baseline metrics
        vertex_count = len(vertices)
        triangle_count = len(triangles) // 3
        log_metric(
            "chunk_mesh_triangles",
            float(triangle_count),
            labels={"chunk_x": chunk_x, "chunk_z": chunk_z, "vertices": vertex_count},
        )