
from typing import Callable, Optional, Dict
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DirectEntry, DirectOptionMenu, DGG
from panda3d.core import TextNode

class POIPropertyPanel(DirectFrame):
    """Panel for POI metadata and object properties."""
    
    def __init__(self, parent):
        super().__init__(
            parent=parent,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.3, 0.3, -0.6, 0.6),
            pos=(0, 0, 0)
        )
        
        # State
        self.current_poi_data = {"name": "Untitled", "type": "custom", "biome": "any"}
        
        # -- POI Metadata Section --
        DirectLabel(
            parent=self,
            text="POI Settings",
            scale=0.05,
            pos=(0, 0, 0.53),
            text_fg=(1, 1, 1, 1)
        )
        
        # Name
        DirectLabel(
            parent=self, text="Name:", scale=0.035, pos=(-0.25, 0, 0.45), text_align=TextNode.ALeft
        )
        self.name_entry = DirectEntry(
            parent=self,
            initialText="Untitled",
            scale=0.035,
            width=12,
            pos=(-0.1, 0, 0.45),
            command=self._on_name_change,
            focusOutCommand=self._on_name_change
        )
        
        # Type
        DirectLabel(
            parent=self, text="Type:", scale=0.035, pos=(-0.25, 0, 0.35), text_align=TextNode.ALeft
        )
        self.type_menu = DirectOptionMenu(
            parent=self,
            scale=0.035,
            items=["custom", "shrine", "camp", "dungeon", "ruin"],
            initialitem=0,
            pos=(-0.1, 0, 0.35),
            command=self._on_type_change,
            frameSize=(-2, 6, -0.5, 1) # Manual sizing
        )
        
        # Biome
        DirectLabel(
            parent=self, text="Biome:", scale=0.035, pos=(-0.25, 0, 0.25), text_align=TextNode.ALeft
        )
        self.biome_menu = DirectOptionMenu(
            parent=self,
            scale=0.035,
            items=["any", "plains", "forest", "desert", "mountain", "canyon", "swamp"],
            initialitem=0,
            pos=(-0.1, 0, 0.25),
            command=self._on_biome_change
        )
        
        # Separator
        DirectFrame(parent=self, frameColor=(0.3,0.3,0.3,1), frameSize=(-0.28, 0.28, -0.001, 0.001), pos=(0,0,0.15))
        
        # -- Selection Properties --
        self.selection_label = DirectLabel(
            parent=self,
            text="No Selection",
            scale=0.045,
            pos=(0, 0, 0.05),
            text_fg=(0.8, 0.8, 0.8, 1)
        )
        
        self.inspector_frame = DirectFrame(
            parent=self,
            frameColor=(0, 0, 0, 0),
            frameSize=(-0.28, 0.28, -0.5, 0),
            pos=(0, 0, 0)
        )
        
    def _on_name_change(self, text):
        self.current_poi_data["name"] = text
        
    def _on_type_change(self, arg):
        self.current_poi_data["type"] = arg
        
    def _on_biome_change(self, arg):
        self.current_poi_data["biome"] = arg
        
    def show_block_properties(self, pos, block_name):
        """Show inspector for block."""
        self.selection_label["text"] = f"Block: {block_name}"
        self._clear_inspector()
        
        DirectLabel(
            parent=self.inspector_frame,
            text=f"Pos: {pos}",
            scale=0.03,
            pos=(0, 0, -0.05)
        )
        
    def show_entity_properties(self, entity_marker):
        """Show inspector for entity."""
        self.selection_label["text"] = f"Entity: {entity_marker.entity_type}"
        self._clear_inspector()
        
        DirectLabel(
            parent=self.inspector_frame,
            text=f"Category: {entity_marker.category}",
            scale=0.03,
            pos=(0, 0, -0.05)
        )
        
        if entity_marker.entity_type == "chest":
            DirectButton(
                parent=self.inspector_frame,
                text="Edit Loot...",
                scale=0.04,
                pos=(0, 0, -0.15),
                command=lambda: print("Loot editor TODO")
            )
            
    def clear_selection(self):
        self.selection_label["text"] = "No Selection"
        self._clear_inspector()
        
    def _clear_inspector(self):
        for child in self.inspector_frame.getChildren():
            child.removeNode()
