"""
EditorSuiteManager: Tab-based editor switching with vertical sidebar.

Manages multiple editors and provides navigation between them.
"""

from typing import Dict, Type, Optional
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DGG
from panda3d.core import TextNode

from engine.editor.selection import EditorSelection
from engine.core.logger import get_logger

logger = get_logger(__name__)


class EditorSuiteManager:
    """Manages multiple editors with vertical sidebar navigation.
    
    Features:
    - Vertical sidebar with numbered buttons
    - Shared selection state
    - Clean transitions between editors
    """
    
    def __init__(self, app):
        """Initialize editor suite manager.
        
        Args:
            app: EditorApp instance
        """
        self.app = app
        self.editors: Dict[str, any] = {}
        self.editor_order: list[str] = []
        self.active_editor: Optional[str] = None
        
        # Shared state
        self.selection = EditorSelection()
        
        # UI
        self._build_sidebar()
        
    def _build_sidebar(self):
        """Build vertical sidebar with editor tabs."""
        # Sidebar container
        self.sidebar = DirectFrame(
            parent=self.app.aspect2d,
            frameColor=(0.1, 0.1, 0.12, 0.95),
            frameSize=(-0.15, 0.15, -0.9, 0.9),
            pos=(-1.15, 0, 0),
            relief=DGG.FLAT
        )
        
        # Title
        DirectLabel(
            parent=self.sidebar,
            text="Editors",
            scale=0.05,
            pos=(0, 0, 0.8),
            text_fg=(0.8, 0.8, 0.8, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        # Tab buttons container
        self.tab_container = DirectFrame(
            parent=self.sidebar,
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.14, 0.14, -0.7, 0.7),
            pos=(0, 0, 0)
        )
        
        self.tab_buttons: Dict[str, DirectButton] = {}
        
    def add_editor(self, name: str, editor_instance):
        """Add an editor to the suite.
        
        Args:
            name: Display name for the editor
            editor_instance: Initialized editor object
        """
        self.editors[name] = editor_instance
        self.editor_order.append(name)
        
        # Give editor access to shared selection
        if hasattr(editor_instance, 'set_selection'):
            editor_instance.set_selection(self.selection)
        
        # Create tab button
        idx = len(self.editor_order)
        y_pos = 0.65 - (idx - 1) * 0.12
        
        btn = DirectButton(
            parent=self.tab_container,
            text=f"{idx}. {name}",
            scale=0.04,
            pos=(0, 0, y_pos),
            frameColor=(0.2, 0.2, 0.25, 1),
            text_fg=(1, 1, 1, 1),
            text_align=TextNode.ACenter,
            command=self.switch_to,
            extraArgs=[name]
        )
        self.tab_buttons[name] = btn
        
        # Bind number key
        self.app.accept(str(idx), self.switch_to, [name])
        
        logger.info(f"Registered editor: {name} (press {idx})")
        
        # If first editor, activate it
        if len(self.editors) == 1:
            self.switch_to(name)
            
    def switch_to(self, name: str):
        """Switch to a specific editor.
        
        Args:
            name: Name of editor to activate
        """
        if name not in self.editors:
            logger.warning(f"Unknown editor: {name}")
            return
            
        # Hide current editor
        if self.active_editor and self.active_editor in self.editors:
            current = self.editors[self.active_editor]
            if hasattr(current, 'hide'):
                current.hide()
            # Update button style
            if self.active_editor in self.tab_buttons:
                self.tab_buttons[self.active_editor]['frameColor'] = (0.2, 0.2, 0.25, 1)
                
        # Show new editor
        self.active_editor = name
        editor = self.editors[name]
        if hasattr(editor, 'show'):
            editor.show()
            
        # Update button style (highlight active)
        if name in self.tab_buttons:
            self.tab_buttons[name]['frameColor'] = (0.3, 0.5, 0.3, 1)
            
        logger.debug(f"Switched to editor: {name}")
        
    def get_active(self):
        """Get the currently active editor.
        
        Returns:
            Active editor instance or None
        """
        if self.active_editor:
            return self.editors.get(self.active_editor)
        return None
        
    def cleanup(self):
        """Clean up all editors and UI."""
        for editor in self.editors.values():
            if hasattr(editor, 'cleanup'):
                editor.cleanup()
                
        if self.sidebar:
            self.sidebar.destroy()
