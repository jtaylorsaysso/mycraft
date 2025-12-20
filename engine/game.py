"""
VoxelGame entry point.
"""
from typing import Optional, Dict, Any, Type
import sys

# Engine imports
from engine.ecs.world import World
from engine.ecs.component import Component
from engine.ecs.system import System
from engine.core.logger import get_logger

# Systems
from engine.systems.lifecycle import DamageSystem, SpawnSystem
from engine.systems.interaction import InventorySystem, TriggerSystem
from engine.systems.logic import PathfindingSystem, TimerSystem
from engine.systems.network import SyncSystem
from engine.voxel.block import Block

logger = get_logger(__name__)

class VoxelGame:
    """
    Simplified entry point for creating voxel games.
    Wraps the ECS/Engine complexity.
    """
    
    def __init__(self, name: str = "My Voxel Game"):
        self.name = name
        self.world = World()
        self.blocks: Dict[str, Block] = {}
        
        # Initialize default systems
        self._setup_default_systems()
        
    def _setup_default_systems(self):
        """Add core systems to the world."""
        # Lifecycle
        self.world.add_system(DamageSystem(self.world, self.world.event_bus))
        self.world.add_system(SpawnSystem(self.world, self.world.event_bus))
        
        # Interaction
        self.world.add_system(InventorySystem(self.world, self.world.event_bus))
        self.world.add_system(TriggerSystem(self.world, self.world.event_bus))
        
        # Logic
        self.world.add_system(PathfindingSystem(self.world, self.world.event_bus))
        self.world.add_system(TimerSystem(self.world, self.world.event_bus))
        
        # Network
        self.world.add_system(SyncSystem(self.world, self.world.event_bus))

    def register_block(self, block: Block):
        """Register a new block type."""
        self.blocks[block.id] = block
        logger.info(f"Registered block: {block.id}")

    def spawn_entity(self, components: list[Component]) -> str:
        """Create an entity with the given components."""
        entity_id = self.world.create_entity()
        for comp in components:
            self.world.add_component(entity_id, comp)
        return entity_id

    def spawn_player(self, position: tuple = (0, 10, 0)):
        """Spawn the player character."""
        from engine.components.core import Transform, Health, Inventory
        
        entity_id = self.world.create_entity(tag="player")
        
        from ursina import Vec3
        pos = Vec3(*position)
        
        self.world.add_component(entity_id, Transform(position=pos))
        self.world.add_component(entity_id, Health(current=100, max_hp=100))
        self.world.add_component(entity_id, Inventory(slots=[None]*9))
        
        logger.info(f"Spawned player at {position}")
        return entity_id

    def run(self):
        """Start the game loop."""
        logger.info(f"Starting {self.name}...")
        
        # Import here to avoid circular dependencies or early Ursina init
        from ursina import Ursina, window, application
        
        app = Ursina(title=self.name, verbose=False)
        
        # Hook update loop
        def update():
            # dt = time.dt 
            dt = 1.0/60.0 # Placeholder fixed timestep
            self.world.update(dt)
            
        # Bind update
        app.update = update # In a real implementation we'd append to update list
        
        # Start
        app.run()

    @classmethod
    def from_config(cls, config_path: str) -> 'VoxelGame':
        """Load a game from a YAML config file."""
        from engine.core.config_loader import load_game_config
        return load_game_config(config_path)
