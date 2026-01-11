"""
Base panel classes for editor UI.

Provides standard sidebar and floating panel containers.
"""

from direct.gui.DirectGui import DirectFrame, DirectLabel, DGG
from panda3d.core import TextNode

from engine.editor.ui.theme import Colors, Spacing, TextScale, FrameSize


class BasePanel:
    """Base class for editor panels.
    
    Provides standard container, header, and lifecycle methods.
    """
    
    def __init__(self, parent, title: str, pos=(0, 0, 0), frame_size=FrameSize.SIDEBAR):
        """
        Initialize panel.
        
        Args:
            parent: Parent GUI node (usually aspect2d)
            title: Panel header text
            pos: Position tuple (x, y, z)
            frame_size: Frame size tuple (left, right, bottom, top)
        """
        self.title = title
        
        # Main container
        self.frame = DirectFrame(
            parent=parent,
            frameColor=Colors.BG_PANEL,
            frameSize=frame_size,
            pos=pos,
            relief=DGG.FLAT
        )
        
        # Header
        self._header = DirectLabel(
            parent=self.frame,
            text=title,
            text_scale=TextScale.HEADER,
            pos=(-frame_size[1] + Spacing.PANEL_PADDING, 0, frame_size[3] - Spacing.PANEL_PADDING),
            text_fg=Colors.TEXT_PRIMARY,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0)
        )
        
        # Content area starts below header
        self._content_start_y = frame_size[3] - Spacing.PANEL_PADDING - Spacing.ITEM_GAP
        
    def show(self):
        """Show the panel."""
        self.frame.show()
        
    def hide(self):
        """Hide the panel."""
        self.frame.hide()
        
    def is_hidden(self) -> bool:
        """Check if panel is hidden."""
        return self.frame.isHidden()
        
    def setPos(self, *args, **kwargs):
        """Proxy setPos to frame."""
        self.frame.setPos(*args, **kwargs)
        
    def setScale(self, *args, **kwargs):
        """Proxy setScale to frame."""
        self.frame.setScale(*args, **kwargs)
        
    def getPos(self, *args, **kwargs):
        """Proxy getPos to frame."""
        return self.frame.getPos(*args, **kwargs)
        
    def getScale(self, *args, **kwargs):
        """Proxy getScale to frame."""
        return self.frame.getScale(*args, **kwargs)
        
    def reparentTo(self, *args, **kwargs):
        """Proxy reparentTo to frame."""
        self.frame.reparentTo(*args, **kwargs)
        
    def cleanup(self):
        """Destroy the panel and all children."""
        self.frame.destroy()


class SidebarPanel(BasePanel):
    """Left or right sidebar panel.
    
    Standard width sidebar with header and scrollable content.
    """
    
    def __init__(self, parent, title: str, side: str = "left"):
        """
        Initialize sidebar.
        
        Args:
            parent: Parent GUI node
            title: Panel header text
            side: "left" or "right"
        """
        x_pos = -1.0 if side == "left" else 1.0
        super().__init__(parent, title, pos=(x_pos, 0, 0), frame_size=FrameSize.SIDEBAR)
        
        # Content frame for scrollable items
        content_height = FrameSize.SIDEBAR[3] - FrameSize.SIDEBAR[2] - Spacing.SECTION_GAP
        self.content = DirectFrame(
            parent=self.frame,
            frameColor=(0, 0, 0, 0),
            frameSize=(
                FrameSize.SIDEBAR[0] + Spacing.PANEL_PADDING,
                FrameSize.SIDEBAR[1] - Spacing.PANEL_PADDING,
                FrameSize.SIDEBAR[2] + Spacing.PANEL_PADDING,
                self._content_start_y
            ),
            pos=(0, 0, 0)
        )


class FloatingPanel(BasePanel):
    """Compact floating panel for tools and controls."""
    
    def __init__(self, parent, title: str, pos=(0, 0, 0)):
        """
        Initialize floating panel.
        
        Args:
            parent: Parent GUI node
            title: Panel header text
            pos: Position tuple
        """
        super().__init__(parent, title, pos=pos, frame_size=FrameSize.COMPACT)
