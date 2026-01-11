
from typing import Callable, Optional
from direct.gui.DirectGui import DirectButton, DGG, DirectFrame
from panda3d.core import TextNode

from engine.editor.ui.theme import Colors, Spacing, TextScale, FrameSize
from engine.editor.ui.base_panel import SidebarPanel
from engine.editor.ui.widgets import EditorLabel

try:
    from games.voxel_world.blocks.blocks import BlockRegistry
except ImportError:
    BlockRegistry = None

class BlockPalette(SidebarPanel):
    """Scrollable palette of available blocks."""
    
    def __init__(self, parent, on_select_callback: Callable[[str], None]):
        super().__init__(parent, title="Blocks", side="left")
        
        self.on_select = on_select_callback
        self.selected_block = None
        self.buttons = {}
        
        # Calculate canvas size logic (dynamic)
        # Using SidebarPanel.content as parent for scrolling? 
        # SidebarPanel doesn't implement scrolling inherently, it gives a content frame.
        # We need to add DirectScrolledFrame inside self.content, OR make SidebarPanel scrollable.
        # Check base_panel.py -> SidebarPanel creates self.content as a DirectFrame.
        
        # We'll put a ScrolledFrame inside self.content
        from direct.gui.DirectGui import DirectScrolledFrame
        
        # Adjust frame size to fit within Sidebar content area
        # Sidebar content area: width ~0.6, height ~1.6
        bg_width = FrameSize.SIDEBAR[1] - FrameSize.SIDEBAR[0]
        
        self.scroll_frame = DirectScrolledFrame(
            parent=self.content,
            frameSize=(-0.28, 0.28, -0.6, 0.45), # Approximate fit
            canvasSize=(-0.25, 0.25, -2.0, 0),
            frameColor=(0, 0, 0, 0),
            scrollBarWidth=0.02,
            pos=(0, 0, -0.2) # Shift down relative to content top
        )
        
        self.refresh()
        
    def refresh(self):
        """Reload blocks from registry."""
        # Clear existing
        for btn in self.buttons.values():
            btn.destroy()
        self.buttons.clear()
        
        if not BlockRegistry:
            return
            
        blocks = BlockRegistry.get_all_blocks()
        sorted_names = sorted(blocks.keys())
        
        # Layout
        y = -0.05
        btn_height = Spacing.ITEM_GAP + 0.02
        
        for name in sorted_names:
            block = blocks[name]
            
            # Color
            color = block.color
            if len(color) == 3:
                color = (*color, 1.0)
            
            btn = DirectButton(
                parent=self.scroll_frame.getCanvas(),
                text=name,
                text_scale=TextScale.LABEL,
                text_align=TextNode.ALeft,
                text_pos=(0.04, -0.015),
                frameColor=Colors.BTN_DEFAULT,
                text_fg=Colors.TEXT_SECONDARY,
                frameSize=(-0.22, 0.22, -0.04, 0.04),
                pos=(0, 0, y),
                command=self._on_click,
                extraArgs=[name],
                relief=DGG.FLAT
            )
            
            # Color indicator
            indicator = DirectFrame(
                parent=btn,
                frameColor=color,
                frameSize=(-0.03, 0.03, -0.03, 0.03),
                pos=(-0.18, 0, 0)
            )
            
            self.buttons[name] = btn
            y -= btn_height
            
        # Resize canvas
        z_min = y + 0.05
        self.scroll_frame["canvasSize"] = (-0.25, 0.25, z_min, 0)
        self.scroll_frame.setCanvasSize()

    def _on_click(self, name):
        """Handle selection."""
        self.set_selected(name)
        if self.on_select:
            self.on_select(name)
            
    def set_selected(self, name):
        """Highlight selected block."""
        if self.selected_block and self.selected_block in self.buttons:
            self.buttons[self.selected_block]["frameColor"] = Colors.BTN_DEFAULT
            self.buttons[self.selected_block]["text_fg"] = Colors.TEXT_SECONDARY
            
        self.selected_block = name
        
        if name and name in self.buttons:
            self.buttons[name]["frameColor"] = Colors.BTN_SELECTED
            self.buttons[name]["text_fg"] = Colors.TEXT_PRIMARY
