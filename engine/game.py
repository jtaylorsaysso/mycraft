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

# Panda3D imports
from direct.showbase.ShowBase import ShowBase
from panda3d.core import LVector3f, WindowProperties

logger = get_logger(__name__)

class VoxelGame(ShowBase):
    """
    Panda3D entry point for voxel games.
    Wraps the ECS/Engine complexity.
    """
    
    def __init__(self, name: str = "My Voxel Game"):
        ShowBase.__init__(self)
        
        # Window setup
        props = WindowProperties()
        props.setTitle(name)
        self.win.requestProperties(props)
        self.disableMouse() # Disable default camera controls
        
        self.name = name
        self.world = World()
        self.blocks: Dict[str, Block] = {}
        
        # Environment and Rendering
        from engine.rendering.environment import EnvironmentManager
        from engine.rendering.texture_atlas import TextureAtlas
        
        self.environment = EnvironmentManager(self)
        self.texture_atlas = TextureAtlas("Spritesheets/terrain.png", self.loader)
        
        # Initialize default systems

        self._setup_default_systems()
        
        # Start game loop
        self.taskMgr.add(self.update_loop, "game_loop")
        
    def update_loop(self, task):
        """Main game loop."""
        dt = globalClock.getDt()
        self.world.update(dt)
        return task.cont

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
        
        # Rendering & World (Phase 6 Integration)
        from games.voxel_world.systems.world_gen import TerrainSystem
        self.world.add_system(TerrainSystem(self.world, self.world.event_bus, self, self.texture_atlas))

        
        from engine.systems.water_physics import WaterPhysicsSystem
        self.world.add_system(WaterPhysicsSystem(self.world, self.world.event_bus))
        
        from engine.systems.input import PlayerControlSystem
        self.world.add_system(PlayerControlSystem(self.world, self.world.event_bus, self))
        
        # Remote player rendering (multiplayer)
        from engine.systems.remote_players import RemotePlayerManager
        self.world.add_system(RemotePlayerManager(self.world, self.world.event_bus, self))
        
        # Tools & Feedback (Added Phase 6)
        from engine.systems.feedback import FeedbackSystem
        self.world.add_system(FeedbackSystem(self.world, self.world.event_bus, self))

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
        
        # Use native Panda3D vector
        pos = LVector3f(*position)
        
        self.world.add_component(entity_id, Transform(position=pos))
        self.world.add_component(entity_id, Health(current=100, max_hp=100))
        self.world.add_component(entity_id, Inventory(slots=[None]*9))
        
        logger.info(f"Spawned player at {position}")
        return entity_id


    @classmethod
    def from_config(cls, config_path: str) -> 'VoxelGame':
        """Load a game from a YAML config file."""
        from engine.core.config_loader import load_game_config
        return load_game_config(config_path)
