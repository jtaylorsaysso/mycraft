from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DirectOptionMenu, DGG
from panda3d.core import TextNode

class ClipBrowserPanel:
    """Left sidebar for managing animation clips."""
    
    def __init__(self, parent, registry, callbacks):
        self.registry = registry
        self.callbacks = callbacks # on_clip_select, on_new, on_save, on_load
        
        # Main container
        self.frame = DirectFrame(
            parent=parent,
            frameColor=(0.12, 0.12, 0.14, 1),
            frameSize=(-0.35, 0.35, -0.9, 0.9),
            pos=(-1.0, 0, 0)
        )
        
        self._build_ui()
        
    def _build_ui(self):
        y = 0.85
        
        # Header
        DirectLabel(
            parent=self.frame,
            text="Clips",
            scale=0.045,
            pos=(-0.3, 0, y),
            text_fg=(0.9, 0.9, 0.9, 1),
            text_align=TextNode.ALeft,
            frameColor=(0,0,0,0)
        )
        y -= 0.1
        
        # Dropdown
        self.clip_dropdown = DirectOptionMenu(
            parent=self.frame,
            items=["(no clips)"],
            scale=0.045,
            pos=(-0.3, 0, y),
            highlightColor=(0.3, 0.3, 0.3, 1),
            command=self.callbacks.get('on_clip_select')
        )
        y -= 0.1
        
        # Refresh
        DirectButton(
            parent=self.frame,
            text="Refresh List",
            scale=0.035,
            pos=(0, 0, y),
            frameSize=(-3, 3, -0.5, 0.8),
            command=self._refresh_list
        )
        y -= 0.15
        
        # Actions
        DirectLabel(
            parent=self.frame,
            text="Actions",
            scale=0.035,
            pos=(-0.3, 0, y),
            text_fg=(0.7, 0.7, 0.7, 1),
            text_align=TextNode.ALeft,
            frameColor=(0,0,0,0)
        )
        y -= 0.08
        
        std_btn_geom = (-2.5, 2.5, -0.5, 0.8)
        
        DirectButton(
            parent=self.frame,
            text="New Clip",
            scale=0.035,
            pos=(0, 0, y),
            frameSize=std_btn_geom,
            frameColor=(0.2, 0.6, 0.2, 1),
            text_fg=(1, 1, 1, 1),
            command=self.callbacks.get('on_new')
        )
        y -= 0.08
        
        DirectButton(
            parent=self.frame,
            text="Save Clip",
            scale=0.035,
            pos=(0, 0, y),
            frameSize=std_btn_geom,
            frameColor=(0.2, 0.5, 0.8, 1),
            text_fg=(1, 1, 1, 1),
            command=self.callbacks.get('on_save')
        )
        y -= 0.08
        
        DirectButton(
            parent=self.frame,
            text="Load Clip",
            scale=0.035,
            pos=(0, 0, y),
            frameSize=std_btn_geom,
            frameColor=(0.4, 0.4, 0.45, 1),
            text_fg=(1, 1, 1, 1),
            command=self.callbacks.get('on_load')
        )
        
    def refresh_clip_list(self):
        """Update dropdown items."""
        self._refresh_list()
        
    def _refresh_list(self):
        clip_names = self.registry.list_clips()
        if not clip_names:
            clip_names = ["(no clips)"]
        self.clip_dropdown['items'] = clip_names
        
    def set_selected(self, name):
        """Set active dropdown item."""
        items = self.clip_dropdown['items']
        if name in items:
            self.clip_dropdown.set(name)
            
    def cleanup(self):
        self.frame.destroy()
