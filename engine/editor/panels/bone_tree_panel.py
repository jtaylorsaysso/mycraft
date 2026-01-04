from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton
from panda3d.core import TextNode

class BoneTreePanel:
    """Left sidebar showing bone hierarchy."""
    
    def __init__(self, parent, selection, bone_display_names):
        self.selection = selection
        self.bone_display_names = bone_display_names
        
        # Main container
        self.frame = DirectFrame(
            parent=parent,
            frameColor=(0.12, 0.12, 0.14, 1),
            frameSize=(-0.35, 0.35, -0.9, 0.9),
            pos=(-1.0, 0, 0)
        )
        
        # Header
        DirectLabel(
            parent=self.frame,
            text="Skeleton",
            scale=0.045,
            pos=(-0.3, 0, 0.85),
            text_fg=(0.9, 0.9, 0.9, 1),
            text_align=TextNode.ALeft,
            frameColor=(0,0,0,0)
        )
        
        self.scroll_frame = DirectFrame(
            parent=self.frame,
            frameColor=(0,0,0,0),
            frameSize=(-0.33, 0.33, -0.85, 0.8),
            pos=(0, 0, 0)
        )
        
        self.bone_buttons = {}
        
    def build_tree(self, skeleton):
        """Build flat list of bones (hierarchical tree TODO)."""
        # Clear existing
        for btn in self.bone_buttons.values():
            btn.destroy()
        self.bone_buttons.clear()
        
        if not skeleton:
            return
            
        y_pos = 0.75
        
        # Simple flat list for now, preserving ModelEditor behavior
        for bone_name in skeleton.bones.keys():
            display = self.bone_display_names.get(bone_name, bone_name.replace('_', ' ').title())
            
            btn = DirectButton(
                parent=self.scroll_frame,
                text=display,
                scale=0.035,
                pos=(-0.3, 0, y_pos),
                frameColor=(0.2, 0.2, 0.22, 1),
                text_fg=(0.8, 0.8, 0.8, 1),
                text_align=TextNode.ALeft,
                frameSize=(-0.02, 0.6, -0.015, 0.035),
                command=self._on_bone_click,
                extraArgs=[bone_name],
                relief=1  # DGG.RAISED
            )
            self.bone_buttons[bone_name] = btn
            y_pos -= 0.09
            
    def _on_bone_click(self, bone_name):
        if self.selection:
            self.selection.bone = bone_name
            self.update_selection(bone_name)
            
    def update_selection(self, selected_bone):
        """Highlight active bone."""
        for name, btn in self.bone_buttons.items():
            if name == selected_bone:
                btn['frameColor'] = (0.2, 0.6, 0.2, 1) # Green
                btn['text_fg'] = (1, 1, 1, 1)
            else:
                btn['frameColor'] = (0.2, 0.2, 0.22, 1)
                btn['text_fg'] = (0.8, 0.8, 0.8, 1)
                
    def cleanup(self):
        self.frame.destroy()
