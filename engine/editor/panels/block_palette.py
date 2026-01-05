
from typing import Callable, Optional
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DGG, DirectScrolledFrame
from panda3d.core import TextNode, Vec4

try:
    from games.voxel_world.blocks.blocks import BlockRegistry
except ImportError:
    BlockRegistry = None

class BlockPalette(DirectFrame):
    """Scrollable palette of available blocks."""
    
    def __init__(self, parent, on_select_callback: Callable[[str], None]):
        super().__init__(
            parent=parent,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.3, 0.3, -0.6, 0.6),
            pos=(0, 0, 0)
        )
        
        self.on_select = on_select_callback
        self.selected_block = None
        self.buttons = {}
        
        # Title
        DirectLabel(
            parent=self,
            text="Blocks",
            scale=0.05,
            pos=(0, 0, 0.53),
            text_fg=(1, 1, 1, 1)
        )
        
        # Scrollable Area
        self.scroll_frame = DirectScrolledFrame(
            parent=self,
            frameSize=(-0.28, 0.28, -0.5, 0.5),
            canvasSize=(-0.25, 0.25, -2.0, 0), # Dynamic resize based on content?
            frameColor=(0, 0, 0, 0.2),
            scrollBarWidth=0.02,
            pos=(0, 0, -0.05)
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
        btn_height = 0.1
        spacing = 0.02
        
        for name in sorted_names:
            block = blocks[name]
            
            # Color
            color = block.color
            if len(color) == 3:
                color = (*color, 1.0)
            
            btn = DirectButton(
                parent=self.scroll_frame.getCanvas(),
                text=name,
                text_scale=0.035,
                text_align=TextNode.ALeft,
                text_pos=(0.04, -0.015),
                frameColor=(0.2, 0.2, 0.2, 1),
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
            y -= (btn_height + spacing)
            
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
            self.buttons[self.selected_block]["frameColor"] = (0.2, 0.2, 0.2, 1)
            
        self.selected_block = name
        
        if name and name in self.buttons:
            self.buttons[name]["frameColor"] = (0.4, 0.4, 0.6, 1)
