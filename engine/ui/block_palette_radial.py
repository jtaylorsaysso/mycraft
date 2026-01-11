"""Block palette using radial menu for in-game block selection.

Provides 2-level navigation:
1. Category selection (Nature, Plants, Building, Utility)
2. Block selection within category
"""

from typing import Optional, Callable
from engine.ui.radial_menu import RadialMenu, RadialMenuItem

try:
    from games.voxel_world.blocks.blocks import BlockRegistry
except ImportError:
    BlockRegistry = None


class BlockPaletteRadial:
    """Manages block selection via radial menu.
    
    Usage:
        palette = BlockPaletteRadial(base, on_block_selected)
        palette.show()  # Shows category menu
        palette.hide()  # Hides menu
    """
    
    def __init__(self, base, on_block_selected: Callable[[str], None]):
        """Initialize block palette.
        
        Args:
            base: ShowBase instance
            on_block_selected: Callback when block is selected (receives block name)
        """
        self.base = base
        self.on_block_selected = on_block_selected
        
        self.radial_menu = RadialMenu(base, radius=0.35)
        self.current_category: Optional[str] = None
        
    def show(self):
        """Show category selection menu."""
        if not BlockRegistry:
            return
            
        categories = BlockRegistry.get_all_categories()
        items = [
            RadialMenuItem(
                id=cat,
                label=cat,
                color=self._get_category_color(cat)
            )
            for cat in categories
        ]
        
        self.radial_menu.show(items, self._on_category_selected)
        self.radial_menu.update_center_label("Select Category")
        self.current_category = None
        
    def hide(self):
        """Hide menu."""
        self.radial_menu.hide()
        self.current_category = None
        
    def _on_category_selected(self, category_id: str):
        """Handle category selection."""
        if category_id == "__back__":
            # Already at top level, just hide
            self.hide()
            return
            
        # Show blocks in this category
        self.current_category = category_id
        blocks = BlockRegistry.get_blocks_by_category(category_id)
        
        items = [
            RadialMenuItem(
                id=block.name,
                label=block.display_name,
                color=block.color
            )
            for block in blocks
        ]
        
        # Hide current menu and show block menu
        self.radial_menu.hide()
        self.radial_menu.show(items, self._on_block_selected)
        self.radial_menu.update_center_label("Back")
        
    def _on_block_selected(self, block_id: str):
        """Handle block selection."""
        if block_id == "__back__":
            # Go back to category menu
            self.radial_menu.hide()
            self.show()
            return
            
        # Block selected - notify callback and hide
        if self.on_block_selected:
            self.on_block_selected(block_id)
        self.hide()
        
    def _get_category_color(self, category: str) -> tuple:
        """Get color for category icon."""
        colors = {
            "Nature": (0.6, 0.5, 0.4),  # Brown
            "Plants": (0.3, 0.7, 0.3),  # Green
            "Building": (0.5, 0.5, 0.6),  # Grey
            "Utility": (0.8, 0.7, 0.3),  # Gold
        }
        return colors.get(category, (0.7, 0.7, 0.7))
