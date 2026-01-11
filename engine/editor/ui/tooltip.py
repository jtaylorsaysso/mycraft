"""
Tooltip widget for editor UI.

Provides hover tooltips for buttons and interactive elements.
"""

from typing import Optional
from direct.gui.DirectGui import DirectLabel, DGG
from panda3d.core import TextNode

from engine.editor.ui.theme import Colors, TextScale


class Tooltip:
    """
    Hover tooltip that follows the mouse.
    
    Usage:
        tooltip = Tooltip(aspect2d)
        button.bind(DGG.ENTER, tooltip.show, ["Button description"])
        button.bind(DGG.EXIT, tooltip.hide)
    """
    
    def __init__(self, parent):
        """
        Initialize tooltip.
        
        Args:
            parent: Parent GUI node (typically aspect2d)
        """
        self.parent = parent
        self._label: Optional[DirectLabel] = None
        self._visible = False
        
    def show(self, description: str, event=None):
        """
        Show tooltip with the given description.
        
        Args:
            description: Text to display
            event: Panda3D event (used to get mouse position)
        """
        if not description:
            return
            
        # Create or update label
        if not self._label:
            self._label = DirectLabel(
                parent=self.parent,
                text="",
                text_scale=TextScale.SMALL,
                text_fg=Colors.TEXT_PRIMARY,
                text_align=TextNode.ALeft,
                frameColor=(0.15, 0.15, 0.15, 0.95),
                pad=(0.015, 0.015),
                relief=DGG.FLAT
            )
            
        self._label["text"] = description
        
        # Position near mouse but offset so it doesn't cover the button
        if event and hasattr(event, 'getMouse'):
            mpos = event.getMouse()
            self._label.setPos(mpos.x + 0.02, 0, mpos.y - 0.05)
        else:
            # Default position
            self._label.setPos(0, 0, -0.8)
            
        self._label.show()
        self._visible = True
        
    def hide(self, event=None):
        """Hide the tooltip."""
        if self._label:
            self._label.hide()
        self._visible = False
        
    def destroy(self):
        """Clean up resources."""
        if self._label:
            self._label.destroy()
            self._label = None
