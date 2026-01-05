"""Game initialization and spawn system.

Handles initial chunk generation, spawn position calculation,
and player entity creation with proper sequencing.
"""

from engine.ecs.system import System
from engine.core.logger import get_logger
from engine.spawn_manager import SpawnManager
from engine.components.core import Transform, Health, Inventory
from panda3d.core import LVector3f
from typing import Optional, Tuple

logger = get_logger(__name__)


class GameSpawnSystem(System):
    """Manages game initialization and player spawning.
    
    This system coordinates:
    1. Initial chunk generation around spawn point
    2. Spawn position calculation
    3. Delayed player entity creation (allows physics to stabilize)
    4. Spawn protection application
    """
    
    def __init__(
        self,
        world,
        event_bus,
        game,
        terrain_system,
        spawn_delay: float = 1.5,
        spawn_point: Optional[Tuple[float, float, float]] = None
    ):
        """Initialize the spawn system.
        
        Args:
            world: ECS world instance
            event_bus: Event bus for system communication
            game: VoxelGame instance
            terrain_system: TerrainSystem for chunk generation
            spawn_delay: Delay in seconds before spawning player (default 1.5s)
            spawn_point: Optional override spawn position
        """
        super().__init__(world, event_bus)
        self.game = game
        self.terrain_system = terrain_system
        self.spawn_delay = spawn_delay
        self.spawn_point_override = spawn_point
        
        # Spawn manager for position calculation
        self.spawn_manager = SpawnManager(world_spawn=(0, 0, 10))
        
        # Initialization state
        self.initialized = False
        self.chunks_generated = False
        self.spawn_scheduled = False
        self.spawn_timer = 0.0
        self.calculated_spawn_pos = None
        
    def _generate_initial_chunks(self):
        """Generate initial 7x7 grid of chunks around origin for better visibility."""
        if self.chunks_generated:
            return
            
        logger.info("🌍 Generating initial chunks...")
        
        # Generate 7x7 grid centered at origin (better exploration visibility)
        # Covers ~112x112 blocks, allowing players to see multiple biomes
        for cx in range(-3, 4):
            for cz in range(-3, 4):
                self.terrain_system.create_chunk(cx, cz)
                logger.debug(f"  ✓ Chunk ({cx}, {cz}) created")
        
        logger.info("✅ Generated 49 chunks around spawn")
        self.chunks_generated = True
    
    def _calculate_spawn_position(self) -> Tuple[float, float, float]:
        """Calculate spawn position using SpawnManager.
        
        Returns:
            Spawn position as (x, y, z) tuple
        """
        # Use override if provided
        if self.spawn_point_override:
            logger.info(f"📍 Using override spawn position: {self.spawn_point_override}")
            return self.spawn_point_override
        
        logger.info("🎯 Calculating spawn position...")
        
        # Get existing players for cooperative spawning
        existing_players = []
        # Get existing players (currently only supports one local player tag)
        player_id = self.world.get_entity_by_tag("player")
        if player_id:
            transform = self.world.get_component(player_id, Transform)
            if transform:
                existing_players.append(transform.position)
        
        # Calculate spawn position
        from games.voxel_world.biomes.biomes import BiomeRegistry
        spawn_pos = self.spawn_manager.find_spawn_position(
            terrain_system=self.terrain_system,
            existing_players=existing_players if existing_players else None,
            biome_registry=BiomeRegistry
        )
        
        logger.info(f"✅ Calculated spawn position: {spawn_pos}")
        return spawn_pos
    
    def _spawn_player(self):
        """Create player entity and apply spawn protection."""
        if not self.calculated_spawn_pos:
            logger.error("Cannot spawn player: no spawn position calculated")
            return
        
        logger.info(f"👤 Spawning player at {self.calculated_spawn_pos}...")
        
        # Create player entity
        self.game.spawn_player(position=self.calculated_spawn_pos)
        
        # SPAWN TEST DUMMY
        dummy_pos = (
            self.calculated_spawn_pos[0] + 5.0, 
            self.calculated_spawn_pos[1] + 5.0, 
            self.calculated_spawn_pos[2]
        )
        dummy = self.world.create_entity()
        self.world.add_component(dummy, Transform(position=LVector3f(*dummy_pos)))
        self.world.add_component(dummy, Health(current=100, max_hp=100))
        # Add visual (placeholder, maybe use a simple model if available, or just rely on physics/debug)
        # For now, without a visual system hook here, it's invisible but targetable.
        logger.info(f"🎯 Spawned Test Dummy at {dummy_pos}")
        
        # Apply spawn protection
        player_id = self.world.get_entity_by_tag("player")
        if player_id:
            health = self.world.get_component(player_id, Health)
            if health:
                health.invulnerable = True
                health.invuln_timer = 3.0  # 3 second protection
                logger.info("🛡️ Spawn protection active for 3 seconds")
        
        logger.info("✅ Player spawned")
    
    def update(self, dt: float):
        """Update spawn system - handles initialization sequence.
        
        Args:
            dt: Delta time since last update
        """
        # Run initialization once
        if not self.initialized:
            self._generate_initial_chunks()
            self.calculated_spawn_pos = self._calculate_spawn_position()
            self.initialized = True
            self.spawn_timer = self.spawn_delay
            logger.info(f"⏳ Waiting {self.spawn_delay}s for terrain to stabilize...")
            return
        
        # Count down spawn timer
        if self.spawn_timer > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self._spawn_player()
                # Disable system after spawning (one-shot initialization)
                self.enabled = False
