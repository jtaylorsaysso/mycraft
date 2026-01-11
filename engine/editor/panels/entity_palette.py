
from typing import Callable, List, Dict
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DGG, DirectScrolledFrame
from panda3d.core import TextNode

class EntityPalette(DirectFrame):
    """Palette for selecting entity markers."""
    
from engine.editor.ui.theme import Colors, Spacing, TextScale, FrameSize
from engine.editor.ui.base_panel import BasePanel
from engine.editor.ui.widgets import EditorLabel, EditorButton

try:
    from engine.entities.entity_registry import EntityRegistry
except ImportError:
    EntityRegistry = None

class EntityPalette(BasePanel):
    """Scrollable palette of available entities."""
    
    def __init__(self, parent, on_select_callback: Callable[[str], None]):
        # Custom smaller size for entity palette (bottom left)
        # Using BasePanel directly to control size
        size = (-0.35, 0.35, -0.5, 0.5) 
        super().__init__(parent, title="Entities", pos=(-1.4, 0, -0.6), frame_size=size)
        
        self.on_select = on_select_callback
        self.selected_entity = None
        self.buttons = {}
        
        # Scrollable Area
        self.scroll_frame = DirectScrolledFrame(
            parent=self.frame,
            frameSize=(-0.33, 0.33, -0.45, 0.4), # Fit inside frame
            canvasSize=(-0.3, 0.3, -2.0, 0),
            frameColor=(0, 0, 0, 0),
            scrollBarWidth=0.02,
            pos=(0, 0, -0.05)
        )
        
        self.refresh()
        
    def refresh(self):
        """Reload entities from registry."""
        # Clear existing
        for btn in self.buttons.values():
            btn.destroy()
        self.buttons.clear()
        
        if not EntityRegistry:
            # Fallback for dev if registry missing
            categories = {
                "Mobs": ["skeleton", "zombie", "spider"],
                "NPCs": ["villager", "trader"],
                "Items": ["chest", "barrel"]
            }
        else:
            categories = EntityRegistry.get_categories() # Hypothetical API
            
        # Layout
        y = -0.05
        
        for category, entities in categories.items():
            # Category Header
            EditorLabel(
                parent=self.scroll_frame.getCanvas(),
                text=category,
                pos=(-0.28, 0, y),
                scale="small",
                color="highlight"
            )
            y -= 0.08
            
            for name in entities:
                btn = EditorButton(
                    parent=self.scroll_frame.getCanvas(),
                    text=name.replace("_", " ").title(),
                    pos=(0, 0, y),
                    command=self._on_click,
                    extraArgs=[name],
                    size="small"
                )
                # Adjust button width
                btn['frameSize'] = (-0.28, 0.28, -0.025, 0.035)
                btn['text_align'] = TextNode.ALeft
                btn['text_pos'] = (-0.25, -0.01)
                
                self.buttons[name] = btn
                y -= 0.07
                
            y -= 0.05 # Gap between categories
            
        # Resize canvas
        z_min = y + 0.05
        self.scroll_frame["canvasSize"] = (-0.3, 0.3, z_min, 0)
        self.scroll_frame.setCanvasSize()

    def _on_click(self, name):
        """Handle selection."""
        self.set_selected(name)
        if self.on_select:
            self.on_select(name)
            
    def set_selected(self, name):
        """Highlight selected entity."""
        if self.selected_entity and self.selected_entity in self.buttons:
            self.buttons[self.selected_entity]["frameColor"] = Colors.BTN_DEFAULT
            self.buttons[self.selected_entity]["text_fg"] = Colors.TEXT_PRIMARY
            
        self.selected_entity = name
        
        if name and name in self.buttons:
            self.buttons[name]["frameColor"] = Colors.BTN_SELECTED
            self.buttons[name]["text_fg"] = Colors.TEXT_HIGHLIGHT
