"""
Manager for in-game editor tools.
"""
from typing import Dict, Optional, Type
from direct.showbase.ShowBase import ShowBase
from engine.ui.base_editor import BaseEditorWindow
from engine.core.logger import get_logger

logger = get_logger(__name__)

class EditorManager:
    """Central manager for all in-game editing tools.
    
    Responsibilities:
    - Registry of available editors
    - Toggling visibility
    - Managing game state (pausing when editing)
    - Handling input shortcuts
    """
    
    def __init__(self, game):
        """Initialize editor manager.
        
        Args:
            game: The VoxelGame instance (needs .base and .set_game_state)
        """
        self.game = game
        self.base = game # ShowBase gets mixed in or inherited
        self.editors: Dict[str, BaseEditorWindow] = {}
        self.active_editor: Optional[BaseEditorWindow] = None
        
    def register_editor(self, name: str, editor_instance: BaseEditorWindow):
        """Register an instantiated editor tool.
        
        Args:
            name: Unique identifier
            editor_instance: The initialized editor window
        """
        self.editors[name] = editor_instance
        logger.info(f"Registered editor tool: {name}")
        
    def toggle_editor(self, name: str):
        """Toggle specific editor visibility and manage game state.
        
        Args:
            name: Name of editor to toggle
        """
        if name not in self.editors:
            logger.warning(f"Attempted to toggle unknown editor: {name}")
            return
            
        target_editor = self.editors[name]
        
        # Case 1: Closing the active editor
        if target_editor == self.active_editor:
            target_editor.hide()
            self.active_editor = None
            self._on_editor_closed()
            
        # Case 2: Opening a new editor (close others if open)
        else:
            if self.active_editor:
                self.active_editor.hide()
            
            target_editor.show()
            self.active_editor = target_editor
            self._on_editor_opened()
            
    def _on_editor_opened(self):
        """Called when any editor becomes active."""
        # Pause game and unlock cursor
        # Note: We import GameState here to avoid circular imports if possible,
        # or rely on the game instance passing enums correctly.
        # Ideally, GameState should be in a shared core module.
        # For now, we assume game has set_game_state and GameState enum access
        from engine.game import GameState
        self.game.set_game_state(GameState.PAUSED)
        logger.info("Editor opened - Game Paused")
        
    def _on_editor_closed(self):
        """Called when all editors are closed."""
        from engine.game import GameState
        self.game.set_game_state(GameState.PLAYING)
        logger.info("Editor closed - Game Resumed")

    def cleanup(self):
        """Clean up all registered editors."""
        for editor in self.editors.values():
            editor.cleanup()
        self.editors.clear()
