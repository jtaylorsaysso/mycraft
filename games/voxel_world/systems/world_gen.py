"""World generation and chunk management using Panda3D."""

from panda3d.core import NodePath, LVector3f, LODNode, TransparencyAttrib
from engine.core.logger import get_logger, time_block, log_metric
from games.voxel_world.biomes.biomes import BiomeRegistry
from games.voxel_world.blocks.blocks import BlockRegistry
from engine.rendering import TextureAtlas, MeshBuilder
from engine.rendering.instancing import InstancedManager
from engine.rendering.shaders import WATER_WOBBLE_SHADER
from engine.ecs.system import System
from typing import Optional, Dict, Tuple, List, Any
import random


class TerrainSystem(System):
    """ECS System that manages chunk generation, loading, and LOD for the voxel world."""
    CHUNK_SIZE = 16
    WATER_LEVEL = 0  # Sea level

    def __init__(self, world, event_bus, base, chunk_load_radius=3, chunk_unload_radius=5, max_chunks_per_frame=1, view_distance=4, config: Optional[Any] = None):
        """Initialize the terrain system.
        
        Args:
            world: ECS World instance
            event_bus: ECS EventBus instance
            base: ShowBase instance
            chunk_load_radius: Load chunks within this radius (in chunks)
            chunk_unload_radius: Unload chunks beyond this radius (in chunks)
            max_chunks_per_frame: For async-ish loading
            view_distance: Max render distance
            config: Optional hot-config
        """
        super().__init__(world, event_bus)
        self.base = base
        self.chunks: Dict[Tuple[int, int], NodePath] = {}
        self.logger = get_logger("terrain")
        self.config = config
        
        self.chunk_load_radius = chunk_load_radius
        self.chunk_unload_radius = chunk_unload_radius
        self.max_chunks_per_frame = max_chunks_per_frame
        self.view_distance = view_distance
        
        self.instancer = InstancedManager(self.base)
        
        # Water rendering
        self.water_meshes: List[NodePath] = []
        self.water_time = 0.0
        
        if self.config:
            self._apply_config()
            self.config.on_change(self._on_config_change)
            
        self.last_player_chunk = None
        self.chunks_to_load = []
        self.chunks_to_unload = []
        
        # Texture atlas
        self.texture_atlas = TextureAtlas("Spritesheets/terrain.png", loader=self.base.loader)
        if self.texture_atlas.is_loaded():
            self.logger.info("Texture atlas loaded successfully")
        else:
            self.logger.warning("Texture atlas failed to load, using color fallback")

    def _apply_config(self):
        """Apply config values."""
        self.chunk_load_radius = self.config.get("chunk_load_radius", self.chunk_load_radius)
        self.chunk_unload_radius = self.config.get("chunk_unload_radius", self.chunk_unload_radius)
        self.max_chunks_per_frame = int(self.config.get("max_chunks_per_frame", self.max_chunks_per_frame))
        self.view_distance = self.config.get("view_distance", self.view_distance)

    def _on_config_change(self, key: str, value):
        """Handle config changes."""
        if key == "chunk_load_radius":
            self.chunk_load_radius = int(value)
            self.last_player_chunk = None 
        elif key == "chunk_unload_radius":
            self.chunk_unload_radius = int(value)
        elif key == "max_chunks_per_frame":
            self.max_chunks_per_frame = int(value)
        elif key == "view_distance":
            self.view_distance = int(value)

    def get_height(self, x, z):
        """Return terrain height at world coordinate (x, z)."""
        biome = BiomeRegistry.get_biome_at(x, z)
        return biome.height_function(x, z)

    def get_player_chunk_coords(self, player_pos):
        """Convert world position to chunk coordinates."""
        if hasattr(player_pos, 'getX'):
            px, pz = player_pos.getX(), player_pos.getZ()
        elif hasattr(player_pos, 'x'):
            px, pz = player_pos.x, player_pos.z
        else:
            px, pz = player_pos[0], player_pos[2]
            
        chunk_x = int(px // self.CHUNK_SIZE)
        chunk_z = int(pz // self.CHUNK_SIZE)
        return (chunk_x, chunk_z)

    def create_chunk(self, chunk_x, chunk_z):
        """Create a single chunk with LOD at (chunk_x, chunk_z)."""
        chunk_size = self.CHUNK_SIZE
        base_x = chunk_x * chunk_size
        base_z = chunk_z * chunk_size
        
        # 1. Generate height and biome data
        heights = [[0 for _ in range(chunk_size)] for _ in range(chunk_size)]
        biomes = [[None for _ in range(chunk_size)] for _ in range(chunk_size)]
        
        for x in range(chunk_size):
            for z in range(chunk_size):
                world_x = base_x + x
                world_z = base_z + z
                heights[x][z] = self.get_height(world_x, world_z)
                biomes[x][z] = BiomeRegistry.get_biome_at(world_x, world_z)
                
        # 2. Setup LOD Node
        lod = LODNode(f'chunk_lod_{chunk_x}_{chunk_z}')
        lod_np = self.base.render.attachNewNode(lod)
        lod_np.setPos(0, 0, 0) # Meshes are in world space for now
        
        # 3. Create Detail Levels
        # High Detail (0 - 100 units)
        high_mesh_node = MeshBuilder.build_chunk_mesh_with_callback(
            heights=heights,
            biomes=biomes,
            chunk_x=chunk_x,
            chunk_z=chunk_z,
            chunk_size=chunk_size,
            texture_atlas=self.texture_atlas,
            block_registry=BlockRegistry,
            get_height_callback=self.get_height
        )
        high_mesh_np = NodePath(high_mesh_node)
        high_mesh_np.reparentTo(lod_np)
        
        if self.texture_atlas.is_loaded():
            high_mesh_np.setTexture(self.texture_atlas.get_texture())
        
        # Simple conservative LOD switches
        # Switch distances (far, near)
        # Level 0 (High): 0 to 128 units
        lod.addSwitch(128, 0)
        
        
        # 4. Generate water mesh based on terrain height and biome
        water_blocks = []
        
        # Cache water system for physics registration
        water_system = self._get_water_system()
        
        for x in range(chunk_size):
            for z in range(chunk_size):
                world_x = base_x + x
                world_z = base_z + z
                h = heights[x][z]
                biome = biomes[x][z]
                
                # Water fills areas below sea level
                if h < self.WATER_LEVEL:
                    for y in range(h + 1, self.WATER_LEVEL + 1):
                        water_blocks.append((x, y, z))
                        if water_system:
                            water_system.register_water_block(world_x, y, world_z)
                
                # Swamps have shallow pools even at ground level if noise permits
                elif biome.name == "swamp":
                    # Simple noise for swamp pools
                    pool_noise = (world_x * 0.3 + world_z * 0.7) % 5
                    if pool_noise < 1.0:
                         water_blocks.append((x, h, z))
                         if water_system:
                            water_system.register_water_block(world_x, h, world_z)
        
        if water_blocks:
            water_mesh_node = MeshBuilder.build_water_mesh(
                water_blocks=water_blocks,
                chunk_x=chunk_x,
                chunk_z=chunk_z,
                chunk_size=chunk_size
            )
            
            if water_mesh_node:
                water_mesh_np = NodePath(water_mesh_node)
                water_mesh_np.reparentTo(lod_np)
                
                # Apply water wobble shader
                water_mesh_np.setShader(WATER_WOBBLE_SHADER)
                water_mesh_np.setShaderInput("time", 0.0)
                water_mesh_np.setShaderInput("wobble_frequency", 2.0)
                water_mesh_np.setShaderInput("wobble_amplitude", 0.08)
                water_mesh_np.setShaderInput("water_alpha", 0.7)
                
                # Enable transparency
                water_mesh_np.setTransparency(TransparencyAttrib.MAlpha)
                water_mesh_np.setBin("transparent", 0)
                water_mesh_np.setDepthWrite(False)
                
                # Track for time updates
                self.water_meshes.append(water_mesh_np)
        
        self.chunks[(chunk_x, chunk_z)] = lod_np
        
        log_metric("chunk_generated", 1.0, labels={"chunk_x": chunk_x, "chunk_z": chunk_z})

    def update(self, dt):
        """Update chunk management based on player position."""
        # Get player position from ECS
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            return
            
        from engine.components.core import Transform
        transform = self.world.get_component(player_id, Transform)
        if not transform:
            return
            
        player_pos = transform.position
        player_chunk = self.get_player_chunk_coords(player_pos)
        
        if self.last_player_chunk != player_chunk:
            self.last_player_chunk = player_chunk
            self._update_chunk_queues(player_chunk)
        
        self._process_loading_queue()
        self._process_unloading_queue()
        
        # Update water wobble animation
        self.water_time += dt
        for water_mesh in self.water_meshes:
            if not water_mesh.isEmpty():
                water_mesh.setShaderInput("time", self.water_time)
    
    def _update_chunk_queues(self, player_chunk):
        """Queue chunks for loading/unloading based on distance."""
        player_cx, player_cz = player_chunk
        
        chunks_to_load = set()
        for cx in range(player_cx - self.chunk_load_radius, player_cx + self.chunk_load_radius + 1):
            for cz in range(player_cz - self.chunk_load_radius, player_cz + self.chunk_load_radius + 1):
                dx, dz = cx - player_cx, cz - player_cz
                if (dx*dx + dz*dz)**0.5 <= self.chunk_load_radius and (cx, cz) not in self.chunks:
                    chunks_to_load.add((cx, cz))
        
        chunks_to_unload = set()
        for coords in self.chunks.keys():
            dx, dz = coords[0] - player_cx, coords[1] - player_cz
            if (dx*dx + dz*dz)**0.5 > self.chunk_unload_radius:
                chunks_to_unload.add(coords)
        
        self.chunks_to_load = sorted(list(chunks_to_load), 
                                     key=lambda c: (c[0]-player_cx)**2 + (c[1]-player_cz)**2)
        self.chunks_to_unload = sorted(list(chunks_to_unload), 
                                       key=lambda c: (c[0]-player_cx)**2 + (c[1]-player_cz)**2, 
                                       reverse=True)

    def _process_loading_queue(self):
        """Generate queued chunks."""
        count = 0
        while self.chunks_to_load and count < self.max_chunks_per_frame:
            coords = self.chunks_to_load.pop(0)
            if coords not in self.chunks:
                self.create_chunk(*coords)
                count += 1

    def _get_water_system(self):
        """Helper to find WaterPhysicsSystem."""
        if hasattr(self, 'water_physics_system') and self.water_physics_system:
            return self.water_physics_system
            
        from engine.systems.water_physics import WaterPhysicsSystem
        if hasattr(self.world, '_systems'):
            for system in self.world._systems:
                if isinstance(system, WaterPhysicsSystem):
                    self.water_physics_system = system
                    return system
        return None

    def _process_unloading_queue(self):
        """Remove distant chunks."""
        count = 0
        while self.chunks_to_unload and count < self.max_chunks_per_frame:
            coords = self.chunks_to_unload.pop(0)
            if coords in self.chunks:
                self.chunks[coords].removeNode()
                del self.chunks[coords]
                count += 1