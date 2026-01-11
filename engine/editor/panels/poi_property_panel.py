from typing import Optional
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectEntry, DirectButton, DGG
from panda3d.core import TextNode

from engine.editor.ui.theme import Colors, Spacing, TextScale, FrameSize
from engine.editor.ui.base_panel import SidebarPanel
from engine.editor.ui.widgets import EditorLabel, EditorButton, EditorDropdown, SectionHeader


class POIPropertyPanel(SidebarPanel):
    """Right sidebar for editing POI properties and metadata."""
    
    def __init__(self, parent, asset_manager=None, on_load=None, on_new=None, on_save=None):
        """
        Initialize POI property panel.
        
        Args:
            parent: Parent GUI node
            asset_manager: AssetManager for listing templates
            on_load: Callback when Load button clicked (receives template name)
            on_new: Callback when New button clicked
            on_save: Callback when Save button clicked
        """
        super().__init__(parent, title="Properties", side="right")
        
        self.asset_manager = asset_manager
        self._on_load_callback = on_load
        self._on_new_callback = on_new
        self._on_save_callback = on_save
        
        self.poi_name = "untitled_poi"
        self.poi_type = "structure"
        self.biome_type = "plains"
        self._selected_template = None
        
        self._build_ui()
        
    def _build_ui(self):
        """Build the property editor UI."""
        y = self._content_start_y
        
        # --- Templates Section ---
        SectionHeader(self.content, "Templates", pos=(0, 0, y))
        y -= 0.08
        
        # Template dropdown
        template_list = self._get_template_list()
        self.template_dropdown = EditorDropdown(
            parent=self.content,
            items=template_list if template_list else ["(no templates)"],
            pos=(-0.02, 0, y),
            command=self._on_template_select
        )
        y -= 0.07
        
        # Load | New buttons row
        EditorButton(
            parent=self.content,
            text="Load",
            pos=(-0.06, 0, y),
            command=self._load_template,
            size="small"
        )
        EditorButton(
            parent=self.content,
            text="New",
            pos=(0.06, 0, y),
            command=self._new_template,
            size="small"
        )
        y -= 0.1
        
        # --- Metadata Section ---
        SectionHeader(self.content, "Metadata", pos=(0, 0, y))
        y -= 0.08
        
        # Name Field
        EditorLabel(
            parent=self.content,
            text="Name:",
            pos=(-0.14, 0, y),
            scale="label",
            align="right"
        )
        
        self.name_entry = DirectEntry(
            parent=self.content,
            scale=TextScale.LABEL,
            pos=(-0.12, 0, y),
            width=8,
            initialText=self.poi_name,
            numLines=1,
            focusInCommand=lambda: None,
            focusOutCommand=self._on_name_change
        )
        y -= 0.08
        
        # Type Dropdown
        EditorLabel(
            parent=self.content,
            text="Type:",
            pos=(-0.14, 0, y),
            scale="label",
            align="right"
        )
        
        self.type_menu = EditorDropdown(
            parent=self.content,
            items=["structure", "village", "dungeon", "landmark"],
            pos=(-0.12, 0, y),
            command=self._on_type_change
        )
        y -= 0.08
        
        # Biome Dropdown
        EditorLabel(
            parent=self.content,
            text="Biome:",
            pos=(-0.14, 0, y),
            scale="label",
            align="right"
        )
        
        self.biome_menu = EditorDropdown(
            parent=self.content,
            items=["plains", "forest", "desert", "mountains", "swamp"],
            pos=(-0.12, 0, y),
            command=self._on_biome_change
        )
        y -= 0.12
        
        # --- Actions ---
        EditorButton(
            parent=self.content,
            text="Save Template",
            pos=(0, 0, y),
            command=self._save_template,
            color="primary",
            size="small"
        )
        
    def _get_template_list(self):
        """Get list of available templates from asset manager."""
        if self.asset_manager:
            return self.asset_manager.list_poi_templates()
        return []
        
    def refresh_templates(self):
        """Refresh the template dropdown list."""
        template_list = self._get_template_list()
        if hasattr(self, 'template_dropdown') and self.template_dropdown:
            # Update dropdown items
            items = template_list if template_list else ["(no templates)"]
            self.template_dropdown['items'] = items
            
    def _on_template_select(self, template_name: str):
        """Handle template selection from dropdown."""
        if template_name != "(no templates)":
            self._selected_template = template_name
            
    def _load_template(self):
        """Load the selected template."""
        if self._selected_template and self._on_load_callback:
            self._on_load_callback(self._selected_template)
            
    def _new_template(self):
        """Create a new template."""
        if self._on_new_callback:
            self._on_new_callback()

    def _on_name_change(self, text):
        self.poi_name = text
        print(f"POI Name set to: {self.poi_name}")
        
    def _on_type_change(self, arg):
        self.poi_type = arg
        print(f"POI Type set to: {self.poi_type}")
        
    def _on_biome_change(self, arg):
        self.biome_type = arg
        print(f"Biome set to: {self.biome_type}")
        
    def _save_template(self):
        print(f"Saving POI Template: {self.poi_name} ({self.poi_type}) in {self.biome_type}")
        # Logic to save to JSON would go here

    @property
    def current_poi_data(self) -> dict:
        """Get current POI metadata as a dict for workspace access."""
        return {
            "name": self.poi_name,
            "type": self.poi_type,
            "biome": self.biome_type
        }
