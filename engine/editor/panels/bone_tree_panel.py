from direct.gui.DirectGui import DirectFrame, DirectButton, DGG
from panda3d.core import TextNode

from engine.editor.ui.theme import Colors, Spacing, TextScale, FrameSize
from engine.editor.ui.widgets import EditorLabel, EditorButton


class BoneTreePanel:
    """Left sidebar showing bone hierarchy."""
    
    def __init__(self, parent, selection, bone_display_names):
        self.selection = selection
        self.bone_display_names = bone_display_names
        
        # Main container
        self.frame = DirectFrame(
            parent=parent,
            frameColor=Colors.BG_PANEL,
            frameSize=FrameSize.SIDEBAR,
            pos=(-1.0, 0, 0)
        )
        
        # Header
        EditorLabel(
            parent=self.frame,
            text="Skeleton",
            pos=(-0.3, 0, 0.85),
            scale="header",
            color="primary"
        )
        
        self.scroll_frame = DirectFrame(
            parent=self.frame,
            frameColor=(0, 0, 0, 0),
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
        
        for bone_name in skeleton.bones.keys():
            display = self.bone_display_names.get(bone_name, bone_name.replace('_', ' ').title())
            
            btn = DirectButton(
                parent=self.scroll_frame,
                text=display,
                text_scale=TextScale.LABEL,
                pos=(-0.3, 0, y_pos),
                frameColor=Colors.BTN_DEFAULT,
                text_fg=Colors.TEXT_SECONDARY,
                text_align=TextNode.ALeft,
                frameSize=(-0.02, 0.6, -0.015, 0.035),
                command=self._on_bone_click,
                extraArgs=[bone_name],
                relief=DGG.FLAT
            )
            self.bone_buttons[bone_name] = btn
            y_pos -= Spacing.ITEM_GAP
            
    def _on_bone_click(self, bone_name):
        if self.selection:
            self.selection.bone = bone_name
            self.update_selection(bone_name)
            
    def update_selection(self, selected_bone):
        """Highlight active bone."""
        for name, btn in self.bone_buttons.items():
            if name == selected_bone:
                btn['frameColor'] = Colors.SELECTION_ACTIVE
                btn['text_fg'] = Colors.TEXT_PRIMARY
            else:
                btn['frameColor'] = Colors.BTN_DEFAULT
                btn['text_fg'] = Colors.TEXT_SECONDARY
                
    def cleanup(self):
        self.frame.destroy()

