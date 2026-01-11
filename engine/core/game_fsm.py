"""
Hierarchical Game State Machine.

Replaces the simple GameState enum with Panda3D FSMs for proper
state management, transition validation, and enter/exit hooks.
"""

from direct.fsm.FSM import FSM
from engine.core.logger import get_logger

logger = get_logger(__name__)


class GameFSM(FSM):
    """Root game state machine.
    
    States:
        MainMenu: In main menu screen
        Playing: Active gameplay (has sub-states via PlayingFSM)
        Paused: Game paused, overlay visible
    
    Manages cursor lock/unlock and input context automatically.
    """
    
    def __init__(self, game):
        FSM.__init__(self, "GameFSM")
        self.game = game
        
        # Valid transitions
        self.defaultTransitions = {
            'MainMenu': ['Playing'],
            'Playing': ['Paused', 'MainMenu'],
            'Paused': ['Playing', 'MainMenu']
        }
    
    # ------------------------------------------------------------------
    # MainMenu State
    # ------------------------------------------------------------------
    
    def enterMainMenu(self):
        """Enter main menu - cursor unlocked, no gameplay."""
        logger.debug("GameFSM: Enter MainMenu")
        self._unlock_cursor()
    
    def exitMainMenu(self):
        """Leave main menu."""
        logger.debug("GameFSM: Exit MainMenu")
    
    # ------------------------------------------------------------------
    # Playing State
    # ------------------------------------------------------------------
    
    def enterPlaying(self):
        """Enter playing mode - cursor locked, physics active."""
        logger.debug("GameFSM: Enter Playing")
        self._lock_cursor()
    
    def exitPlaying(self):
        """Leave playing mode."""
        logger.debug("GameFSM: Exit Playing")
    
    # ------------------------------------------------------------------
    # Paused State
    # ------------------------------------------------------------------
    
    def enterPaused(self):
        """Enter paused mode - cursor unlocked, physics frozen."""
        logger.debug("GameFSM: Enter Paused")
        self._unlock_cursor()
    
    def exitPaused(self):
        """Leave paused mode."""
        logger.debug("GameFSM: Exit Paused")
    
    # ------------------------------------------------------------------
    # Cursor Management
    # ------------------------------------------------------------------
    
    def _lock_cursor(self):
        """Lock and hide cursor for gameplay."""
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.lock_mouse()
    
    def _unlock_cursor(self):
        """Unlock and show cursor for UI."""
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.unlock_mouse()


class PlayingFSM(FSM):
    """Sub-states within Playing mode.
    
    States:
        Exploring: Normal gameplay (default)
        InDialogue: NPC conversation (future)
        InCutscene: Non-interactive sequence (future)
        InInventory: Inventory/chest open
    
    Each sub-state can configure input blocking and UI visibility.
    """
    
    def __init__(self, game):
        FSM.__init__(self, "PlayingFSM")
        self.game = game
        
        # Valid transitions - Exploring is the hub state
        self.defaultTransitions = {
            'Exploring': ['InDialogue', 'InCutscene', 'InInventory', 'Building'],
            'InDialogue': ['Exploring'],
            'InCutscene': ['Exploring'],
            'InInventory': ['Exploring'],
            'Building': ['Exploring']
        }
    
    # ------------------------------------------------------------------
    # Exploring State (Default)
    # ------------------------------------------------------------------
    
    def enterExploring(self):
        """Enter normal exploration - full player control."""
        logger.debug("PlayingFSM: Enter Exploring")
    
    def exitExploring(self):
        """Leave exploration."""
        logger.debug("PlayingFSM: Exit Exploring")
    
    # ------------------------------------------------------------------
    # InDialogue State (Future)
    # ------------------------------------------------------------------
    
    def enterInDialogue(self):
        """Enter dialogue - movement locked, dialogue UI visible."""
        logger.debug("PlayingFSM: Enter InDialogue")
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.block_input("dialogue")
    
    def exitInDialogue(self):
        """Leave dialogue."""
        logger.debug("PlayingFSM: Exit InDialogue")
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.unblock_input("dialogue")
    
    # ------------------------------------------------------------------
    # InCutscene State (Future)
    # ------------------------------------------------------------------
    
    def enterInCutscene(self):
        """Enter cutscene - all input locked, watching sequence."""
        logger.debug("PlayingFSM: Enter InCutscene")
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.block_input("cutscene")
    
    def exitInCutscene(self):
        """Leave cutscene."""
        logger.debug("PlayingFSM: Exit InCutscene")
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.unblock_input("cutscene")
    
    # ------------------------------------------------------------------
    # InInventory State
    # ------------------------------------------------------------------
    
    def enterInInventory(self):
        """Enter inventory - movement locked, inventory UI visible."""
        logger.debug("PlayingFSM: Enter InInventory")
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.block_input("inventory")
    
    def exitInInventory(self):
        """Leave inventory."""
        logger.debug("PlayingFSM: Exit InInventory")
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.unblock_input("inventory")

    # ------------------------------------------------------------------
    # Building State
    # ------------------------------------------------------------------
    
    def enterBuilding(self):
        """Enter build mode - combat/attacks disabled, building enabled."""
        logger.debug("PlayingFSM: Enter Building")
        # Don't block input - we want camera and movement to work
        # BlockPlacerMechanic has its own enabled flag
        
        # Publish event for UI feedback
        if hasattr(self.game, 'world') and hasattr(self.game.world, 'event_bus'):
            self.game.world.event_bus.publish("build_mode_changed", enabled=True)
    
    def exitBuilding(self):
        """Leave build mode."""
        logger.debug("PlayingFSM: Exit Building")
        # Publish event for UI feedback
        if hasattr(self.game, 'world') and hasattr(self.game.world, 'event_bus'):
            self.game.world.event_bus.publish("build_mode_changed", enabled=False)

