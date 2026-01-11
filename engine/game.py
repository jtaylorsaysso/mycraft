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
from engine.input.manager import InputManager
from engine.input.keybindings import KeyBindingManager

# Animation registry (for future use)
from engine.animation.animation_registry import get_animation_registry

# Note: Editors have been moved to standalone suite - use run_editor.py

# Panda3D imports
from direct.showbase.ShowBase import ShowBase
from panda3d.core import LVector3f, WindowProperties

logger = get_logger(__name__)


# Import hierarchical FSM (replaces simple GameState enum)
from engine.core.game_fsm import GameFSM, PlayingFSM


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
        if self.win:
            self.win.requestProperties(props)
        self.disableMouse() # Disable default camera controls
        
        self.name = name
        self.config_manager = config_manager
        self.world = World()
        self.blocks: Dict[str, Block] = {}
        
        # Input Management (Centralized)
        self.key_binding_manager = KeyBindingManager()
        self.input_manager = InputManager(self, self.key_binding_manager)
        
        # Hierarchical game state management (FSM)
        self.game_fsm = GameFSM(self)
        self.playing_fsm = PlayingFSM(self)
        
        # Start in Playing > Exploring state
        self.game_fsm.request('Playing')
        self.playing_fsm.request('Exploring')
        
        # Core key bindings
        self.accept('f9', self.take_screenshot)
        
        # Note: Editors moved to standalone suite - run 'python run_editor.py'
        
        # Environment and Rendering
        from engine.rendering.environment import EnvironmentManager
        from engine.rendering.texture_atlas import TextureAtlas
        from engine.rendering.skybox import Skybox
        
        self.environment = EnvironmentManager(self)
        self.texture_atlas = TextureAtlas("Spritesheets/terrain.png", self.loader)
        
        # Initialize Skybox
        self.skybox = Skybox(self.render, self.loader)
        self.skybox.setup_simple_atmosphere(self)
        
        # Initialize default systems
        self._setup_default_systems()
        
        # Start game loop
        self.taskMgr.add(self.update_loop, "game_loop")
        
    def update_loop(self, task):
        """Main game loop."""
        dt = globalClock.getDt()
        
        # Always update UI systems (they need to handle pause menu, etc)
        # Only update gameplay systems when in Playing state
        is_playing = self.game_fsm.state == 'Playing'
        
        for system in self.world._systems:
            if not system.enabled or not system.ready:
                continue
                
            # UI systems always update
            if system.__class__.__name__ in ['UISystem', 'FeedbackSystem']:
                system.update(dt)
            # Gameplay systems only update when Playing
            elif is_playing:
                system.update(dt)
        
        return task.cont
    
    @property
    def game_state(self) -> str:
        """Get current game state (FSM state name)."""
        return self.game_fsm.state
    
    def set_game_state(self, new_state: str):
        """Request game state transition.
        
        Args:
            new_state: Target state name ('Playing', 'Paused', 'MainMenu')
        """
        self.game_fsm.request(new_state)
    
    def toggle_pause(self):
        """Toggle between Playing and Paused states."""
        if self.game_fsm.state == 'Playing':
            self.game_fsm.request('Paused')
        elif self.game_fsm.state == 'Paused':
            self.game_fsm.request('Playing')
    
    def take_screenshot(self):
        """Capture and save screenshot."""
        # Use Panda3D's automatic screenshot naming
        success = self.screenshot()
        if success:
            print("📸 Screenshot saved to game directory")
        else:
            print("❌ Screenshot failed - check console for errors")

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
        
        # Build Zone Management
        from engine.systems.claim_system import ClaimSystem
        self.claim_system = ClaimSystem(self.world, self.world.event_bus, self.render)
        self.world.add_system(self.claim_system)

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
        from engine.components.core import Transform, Health, Inventory, Stamina, CombatState, KinematicState, CameraState, CameraMode
        from engine.components.avatar_colors import AvatarColors
        
        # Create entity WITHOUT tag first to prevent early system wakeup
        entity_id = self.world.create_entity() # tag="player" removed
        
        # Use native Panda3D vector
        pos = LVector3f(*position)
        
        self.world.add_component(entity_id, Transform(position=pos))
        self.world.add_component(entity_id, Health(current=100, max_hp=100))
        self.world.add_component(entity_id, Inventory(slots=[None]*9))
        self.world.add_component(entity_id, Stamina())  # Add stamina for combat/traversal
        self.world.add_component(entity_id, CombatState())  # Add combat state for action tracking
        self.world.add_component(entity_id, KinematicState())  # Add physics state
        self.world.add_component(entity_id, CameraState(  # Add camera state
            mode=CameraMode.EXPLORATION,
            yaw=0.0,
            pitch=-15.0,
            distance=5.0,
            current_distance=5.0
        ))
        self.world.add_component(entity_id, AvatarColors())  # Add color customization
        
        # Now register tag to wake up systems (PlayerControlSystem)
        self.world.register_tag(entity_id, "player")
        
        # Create initial build zone at spawn location
        if hasattr(self, 'claim_system') and self.claim_system:
            spawn_center = (int(position[0]), int(position[1]), int(position[2]))
            self.claim_system.claim_zone(entity_id, spawn_center, radius=8)
            logger.info(f"✅ Created starter build zone at {spawn_center}")
        
        logger.info(f"Spawned player at {position}")
        return entity_id


    @classmethod
    def from_config(cls, config_path: str) -> 'VoxelGame':
        """Load a game from a YAML config file."""
        from engine.core.config_loader import load_game_config
        return load_game_config(config_path)
