"""
Workspace Base Class

Base class for all editor workspaces (Character, Animation, Preview).
Manages panels and visibility.
"""

from typing import Optional
from direct.showbase.DirectObject import DirectObject
from engine.core.logger import get_logger

logger = get_logger(__name__)

class Workspace(DirectObject):
    """Base class for editor workspaces."""
    
    def __init__(self, app, name: str):
        """Initialize workspace.
        
        Args:
            app: EditorApp instance
            name: Display name of the workspace
        """
        self.app = app
        self.name = name
        self.active = False
        
        # Shared selection from app
        self.selection = None
        if hasattr(app, 'suite_manager'):
             self.selection = app.suite_manager.selection
             
    def set_selection(self, selection):
        """Set shared selection state."""
        self.selection = selection

    def enter(self):
        """Called when workspace becomes active."""
        self.active = True
        logger.debug(f"Entering workspace: {self.name}")
        self.accept_shortcuts()

    def exit(self):
        """Called when switching away from workspace."""
        self.active = False
        logger.debug(f"Exiting workspace: {self.name}")
        self.ignore_all() # Cleanup shortcuts

    def update(self, dt: float):
        """Per-frame update."""
        pass
        
    def accept_shortcuts(self):
        """Register workspace-specific shortcuts. Override in subclasses."""
        pass

    def cleanup(self):
        """Clean up resources."""
        self.ignore_all()
