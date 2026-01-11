"""Radial menu UI component for block selection.

Provides a circular menu that appears when Tab is held, allowing
quick selection from categories and blocks.
"""

from typing import List, Optional, Callable, Tuple
from direct.gui.DirectGui import DirectFrame, DirectButton, DGG
from panda3d.core import TextNode, Vec3
import math


class RadialMenuItem:
    """Single item in a radial menu."""
    
    def __init__(self, id: str, label: str, color: Tuple[float, float, float] = (1, 1, 1)):
        self.id = id
        self.label = label
        self.color = color


class RadialMenu:
    """Circular selection menu that appears on key hold.
    
    Features:
    - 2-level navigation (categories -> items)
    - Mouse-based selection
    - Visual feedback for highlighted item
    """
    
    def __init__(self, base, radius: float = 0.3):
        """Initialize radial menu.
        
        Args:
            base: ShowBase instance
            radius: Radius of menu circle in screen units
        """
        self.base = base
        self.radius = radius
        self.visible = False
        self.selected_index = -1
        
        # Current menu state
        self.current_items: List[RadialMenuItem] = []
        self.on_select_callback: Optional[Callable[[str], None]] = None
        
        # UI elements
        self.root = None
        self.item_buttons: List[DirectButton] = []
        self.center_button = None
        
    def show(self, items: List[RadialMenuItem], on_select: Callable[[str], None]):
        """Display menu with given items.
        
        Args:
            items: List of menu items to display
            on_select: Callback when item is selected (receives item id)
        """
        if self.visible:
            return
            
        self.current_items = items
        self.on_select_callback = on_select
        self.visible = True
        
        # Create root node
        self.root = DirectFrame(
            parent=self.base.aspect2d,
            frameColor=(0, 0, 0, 0),
            frameSize=(-2, 2, -2, 2),
            pos=(0, 0, 0)
        )
        
        # Create center button (for "Back" navigation)
        self.center_button = DirectButton(
            parent=self.root,
            text="",
            text_scale=0.05,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.2, 0.2, 0.2, 0.9),
            frameSize=(-0.08, 0.08, -0.08, 0.08),
            pos=(0, 0, 0),
            command=self._on_center_click,
            relief=DGG.FLAT
        )
        
        # Create item buttons in circle
        num_items = len(items)
        for i, item in enumerate(items):
            angle = (2 * math.pi * i / num_items) - (math.pi / 2)  # Start at top
            x = self.radius * math.cos(angle)
            z = self.radius * math.sin(angle)
            
            # Create button
            btn = DirectButton(
                parent=self.root,
                text=item.label,
                text_scale=0.04,
                text_align=TextNode.ACenter,
                text_fg=(1, 1, 1, 1),
                frameColor=(*item.color, 0.8),
                frameSize=(-0.12, 0.12, -0.05, 0.05),
                pos=(x, 0, z),
                command=self._on_item_click,
                extraArgs=[i],
                relief=DGG.FLAT
            )
            self.item_buttons.append(btn)
        
        # Enable mouse
        self.base.enableMouse()
        
    def hide(self) -> Optional[str]:
        """Hide menu and return selected item id.
        
        Returns:
            Selected item id, or None if nothing selected
        """
        if not self.visible:
            return None
            
        selected_id = None
        if 0 <= self.selected_index < len(self.current_items):
            selected_id = self.current_items[self.selected_index].id
        
        # Clean up UI
        if self.root:
            self.root.destroy()
            self.root = None
        self.item_buttons.clear()
        self.center_button = None
        
        self.visible = False
        self.selected_index = -1
        self.current_items = []
        
        # Disable mouse
        self.base.disableMouse()
        
        return selected_id
    
    def _on_item_click(self, index: int):
        """Handle item button click."""
        self.selected_index = index
        if self.on_select_callback:
            item_id = self.current_items[index].id
            self.on_select_callback(item_id)
    
    def _on_center_click(self):
        """Handle center button click (back navigation)."""
        if self.on_select_callback:
            self.on_select_callback("__back__")
    
    def update_center_label(self, label: str):
        """Update center button text (e.g., 'Back', 'Select Category')."""
        if self.center_button:
            self.center_button["text"] = label
    
    def highlight_item(self, index: int):
        """Highlight an item (for mouse-over effects)."""
        # Reset all
        for btn in self.item_buttons:
            btn["frameColor"] = (*self.current_items[self.item_buttons.index(btn)].color, 0.8)
        
        # Highlight selected
        if 0 <= index < len(self.item_buttons):
            self.item_buttons[index]["frameColor"] = (1, 1, 0, 0.9)  # Yellow highlight
