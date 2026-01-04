
from typing import Callable, List, Dict
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DGG, DirectScrolledFrame
from panda3d.core import TextNode

class EntityPalette(DirectFrame):
    """Palette for selecting entity markers."""
    
    ENTITY_TYPES = [
        # Enemies
        {"id": "skeleton", "name": "Skeleton", "category": "Enemy"},
        {"id": "zombie", "name": "Zombie", "category": "Enemy"},
        
        # Interactive
        {"id": "chest", "name": "Loot Chest", "category": "Interactive"},
        {"id": "shrine_interact", "name": "Shrine Trigger", "category": "Interactive"},
        
        # Markers
        {"id": "spawn", "name": "Player Spawn", "category": "Marker"},
        {"id": "patrol_point", "name": "Patrol Point", "category": "Marker"},
    ]
    
    def __init__(self, parent, on_select_callback: Callable[[str], None]):
        super().__init__(
            parent=parent,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.3, 0.3, -0.6, 0.6),
            pos=(0, 0, 0)
        )
        
        self.on_select = on_select_callback
        self.selected_type = None
        self.buttons = {}
        
        # Title
        DirectLabel(
            parent=self,
            text="Entities",
            scale=0.05,
            pos=(0, 0, 0.53),
            text_fg=(1, 1, 1, 1)
        )
        
        self.scroll_frame = DirectScrolledFrame(
            parent=self,
            frameSize=(-0.28, 0.28, -0.5, 0.5),
            canvasSize=(-0.25, 0.25, -2.0, 0),
            frameColor=(0, 0, 0, 0.2),
            scrollBarWidth=0.02,
            pos=(0, 0, -0.05)
        )
        
        self._build_list()
        
    def _build_list(self):
        y = -0.05
        current_cat = None
        
        for entity in self.ENTITY_TYPES:
            cat = entity["category"]
            
            # Category Header
            if cat != current_cat:
                DirectLabel(
                    parent=self.scroll_frame.getCanvas(),
                    text=cat,
                    text_scale=0.04,
                    text_align=TextNode.ALeft,
                    text_fg=(0.7, 0.7, 0.7, 1),
                    pos=(-0.2, 0, y)
                )
                y -= 0.06
                current_cat = cat
            
            # Button
            btn = DirectButton(
                parent=self.scroll_frame.getCanvas(),
                text=entity["name"],
                text_scale=0.035,
                text_align=TextNode.ALeft,
                text_pos=(0.04, -0.015),
                frameColor=(0.2, 0.2, 0.2, 1),
                frameSize=(-0.22, 0.22, -0.04, 0.04),
                pos=(0, 0, y),
                command=self._on_click,
                extraArgs=[entity["id"]],
                relief=DGG.FLAT
            )
            
            # Icon placeholder
            DirectFrame(
                parent=btn,
                frameColor=(0.5, 0.5, 0.5, 1),
                frameSize=(-0.02, 0.02, -0.02, 0.02),
                pos=(-0.18, 0, 0)
            )
            
            self.buttons[entity["id"]] = btn
            y -= 0.1
            
        z_min = y + 0.05
        self.scroll_frame["canvasSize"] = (-0.25, 0.25, z_min, 0)
        self.scroll_frame.setCanvasSize()

    def _on_click(self, type_id):
        self.set_selected(type_id)
        if self.on_select:
            self.on_select(type_id)
            
    def set_selected(self, type_id):
        if self.selected_type and self.selected_type in self.buttons:
            self.buttons[self.selected_type]["frameColor"] = (0.2, 0.2, 0.2, 1)
            
        self.selected_type = type_id
        
        if type_id in self.buttons:
            self.buttons[type_id]["frameColor"] = (0.4, 0.4, 0.6, 1)
