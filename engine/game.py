"""
VoxelGame entry point.
"""
from typing import Optional, Dict, Any, Type
from enum import Enum, auto
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
from engine.input.manager import InputManager
from engine.input.keybindings import KeyBindingManager

# Panda3D imports
from direct.showbase.ShowBase import ShowBase
from panda3d.core import LVector3f, WindowProperties

logger = get_logger(__name__)


class GameState(Enum):
    """Game state for pause/menu management.
    
    Controls cursor locking and physics updates:
    - PLAYING: Cursor locked, physics active
    - PAUSED: Cursor unlocked, physics frozen, menu visible
    - MENU: Cursor unlocked, physics frozen, in menu screen
    """
    PLAYING = auto()
    PAUSED = auto()
    MENU = auto()


class VoxelGame(ShowBase):
    """
    Panda3D entry point for voxel games.
    Wraps the ECS/Engine complexity.
    """
    
    def __init__(self, name: str = "My Voxel Game", config_manager: Any = None):
        ShowBase.__init__(self)
        
        # Window setup
        props = WindowProperties()
        props.setTitle(name)
        self.win.requestProperties(props)
        self.disableMouse() # Disable default camera controls
        
        self.name = name
        self.config_manager = config_manager
        self.world = World()
        self.blocks: Dict[str, Block] = {}
        
        # Input Management (Centralized)
        self.key_binding_manager = KeyBindingManager()
        self.input_manager = InputManager(self, self.key_binding_manager)
        
        # Game state management
        self._game_state = GameState.PLAYING
        
        # Lock cursor for initial PLAYING state
        # (set_game_state not called during init, so we lock manually)
        self.input_manager.lock_mouse()
        
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
        # print(f"DEBUG: update_loop called, game_state={self._game_state.name}")  # Too spammy
        dt = globalClock.getDt()
        
        # Always update UI systems (they need to handle pause menu, etc)
        # Only update gameplay systems when PLAYING
        for system in self.world._systems:
            if not system.enabled or not system.ready:
                continue
                
            # UI systems always update
            if system.__class__.__name__ in ['UISystem', 'FeedbackSystem']:
                system.update(dt)
            # Gameplay systems only update when PLAYING
            elif self._game_state == GameState.PLAYING:
                system.update(dt)
        
        return task.cont
    
    @property
    def game_state(self) -> GameState:
        """Get current game state."""
        return self._game_state
    
    def set_game_state(self, new_state: GameState):
        """Set game state and manage cursor automatically.
        
        Args:
            new_state: The new game state
        """
        if new_state == self._game_state:
            return
        
        old_state = self._game_state
        self._game_state = new_state
        
        # Auto cursor management based on state
        if new_state == GameState.PLAYING:
            self._lock_cursor()
            logger.debug("Game state: PLAYING (cursor locked, physics active)")
        else:  # PAUSED or MENU
            self._unlock_cursor()
            logger.debug(f"Game state: {new_state.name} (cursor unlocked, physics frozen)")
    
    def toggle_pause(self):
        """Toggle between PLAYING and PAUSED states."""
        if self._game_state == GameState.PLAYING:
            self.set_game_state(GameState.PAUSED)
        elif self._game_state == GameState.PAUSED:
            self.set_game_state(GameState.PLAYING)
    
    def _lock_cursor(self):
        """Lock and hide cursor for gameplay."""
        self.input_manager.lock_mouse()
    
    def _unlock_cursor(self):
        """Unlock and show cursor for UI interaction."""
        self.input_manager.unlock_mouse()

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
        
        # Rendering & World
        # Note: Terrain system is now registered by games via register_terrain_system()
        
        
        from engine.systems.water_physics import WaterPhysicsSystem
        self.world.add_system(WaterPhysicsSystem(self.world, self.world.event_bus))
        
        # UI & HUD (Added Phase 2)
        from engine.systems.ui_system import UISystem
        self.world.add_system(UISystem(self.world, self.world.event_bus, self, self.config_manager))

        # Player Control System (Composition-based mechanics)
        from engine.systems.player_controller import PlayerControlSystem
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
    
    def register_terrain_system(self, terrain_system: System):
        """Register a game-specific terrain system.
        
        This allows games to inject their terrain generation logic
        while maintaining clean engine/game boundaries.
        
        Args:
            terrain_system: Game-specific terrain/chunk system
        """
        self.world.add_system(terrain_system)
        logger.info(f"Registered terrain system: {terrain_system.__class__.__name__}")

    def spawn_entity(self, components: list[Component]) -> str:
        """Create an entity with the given components."""
        entity_id = self.world.create_entity()
        for comp in components:
            self.world.add_component(entity_id, comp)
        return entity_id

    def spawn_player(self, position: tuple = (0, 10, 0)):
        """Spawn the player character."""
        from engine.components.core import Transform, Health, Inventory, KinematicState, CameraState, CameraMode
        
        # Create entity WITHOUT tag first to prevent early system wakeup
        entity_id = self.world.create_entity() # tag="player" removed
        
        # Use native Panda3D vector
        pos = LVector3f(*position)
        
        self.world.add_component(entity_id, Transform(position=pos))
        self.world.add_component(entity_id, Health(current=100, max_hp=100))
        self.world.add_component(entity_id, Inventory(slots=[None]*9))
        self.world.add_component(entity_id, KinematicState())  # Add physics state
        self.world.add_component(entity_id, CameraState(  # Add camera state
            mode=CameraMode.THIRD_PERSON,
            yaw=0.0,
            pitch=-15.0,
            distance=5.0,
            current_distance=5.0
        ))
        
        # Now register tag to wake up systems (PlayerControlSystem)
        self.world.register_tag(entity_id, "player")
        
        logger.info(f"Spawned player at {position}")
        return entity_id


    @classmethod
    def from_config(cls, config_path: str) -> 'VoxelGame':
        """Load a game from a YAML config file."""
        from engine.core.config_loader import load_game_config
        return load_game_config(config_path)
