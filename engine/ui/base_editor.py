"""
Base class for all in-game editor tools.
"""
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectFrame
from panda3d.core import NodePath
from typing import Optional, Any
import abc

from direct.showbase.DirectObject import DirectObject

class BaseEditorWindow(DirectObject):
    """
    Abstract base class for all editor windows.
    
    Standardizes lifecycle management and UI container handling for all
    in-game tools (Animation Editor, Map Editor, etc).
    """
    
    def __init__(self, base_app: ShowBase, name: str):
        """Initialize the editor window.
        
        Args:
            base_app: The Panda3D ShowBase application instance
            name: Unique identifier for this editor
        """
        self.base = base_app
        self.name = name
        self.visible = False
        self.main_frame: Optional[DirectFrame] = None
        
        # UI Configuration
        self.ui_root = self.base.aspect2d
        
        # Run setup immediately
        self.setup()
        
        # Start hidden by default
        self.hide()
        
    @abc.abstractmethod
    def setup(self):
        """Initialize UI components. Must be implemented by subclasses."""
        pass
        
    def show(self):
        """Make the editor visible."""
        if self.main_frame:
            self.main_frame.show()
        self.visible = True
        
    def hide(self):
        """Hide the editor."""
        if self.main_frame:
            self.main_frame.hide()
        self.visible = False
        
    def toggle(self):
        """Toggle visibility state."""
        if self.visible:
            self.hide()
        else:
            self.show()
            
    def cleanup(self):
        """Clean up resources and destroy UI."""
        if self.main_frame:
            self.main_frame.destroy()
            self.main_frame = None
