"""
SliderPanel: Precision control component for ModelEditor.
"""

from typing import Optional, Dict, Callable
from panda3d.core import LVector3f, TextNode
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DirectSlider, DGG
)

from engine.editor.tools.common.editor_history import EditorHistory, EditorCommand
from engine.core.logger import get_logger

logger = get_logger(__name__)

# Theme Colors (duplicated for now to avoid circular imports if we imported from model_editor)
COLOR_PANEL_BG = (0.12, 0.12, 0.14, 0.95)
COLOR_HEADER_BG = (0.18, 0.18, 0.20, 1.0)
COLOR_BUTTON = (0.22, 0.22, 0.26, 1)
COLOR_LABEL = (0.8, 0.8, 0.8, 1)


class SliderPanel:
    """Collapsible panel with precision sliders for bone transforms.
    
    Handles:
    - Position (X, Y, Z)
    - Rotation (H, P, R)
    - Scale/Length
    - Undo/Redo command generation
    - Symmetry application
    """
    
    def __init__(self, parent_node, editor):
        """Initialize slider panel.
        
        Args:
            parent_node: Parent GUI node
            editor: Reference to ModelEditor (controller)
        """
        self.parent_node = parent_node
        self.editor = editor
        self.visible = False
        
        # UI Elements
        self.frame: Optional[DirectFrame] = None
        self.toggle_btn: Optional[DirectButton] = None
        self.position_sliders = {}
        self.rotation_sliders = {}
        self.length_slider = None
        
        self._build_ui()
        self.hide()
        
    def _build_ui(self):
        """Build the panel UI."""
        # Toggle button (always visible)
        self.toggle_btn = DirectButton(
            parent=self.parent_node,
            text="▼ Precision Sliders",
            scale=0.035,
            pos=(1.05, 0, -0.2),
            text_align=TextNode.ALeft,
            frameColor=COLOR_BUTTON,
            text_fg=(1, 1, 1, 1),
            command=self.toggle
        )
        
        # Main Panel
        self.frame = DirectFrame(
            parent=self.parent_node,
            frameColor=COLOR_PANEL_BG,
            frameSize=(-0.35, 0.35, -0.5, 0.5),
            pos=(1.0, 0, -0.6)
        )
        
        y = 0.45
        
        # Position Group
        DirectLabel(
            parent=self.frame,
            text="Position",
            scale=0.04,
            pos=(0, 0, y),
            text_fg=COLOR_LABEL,
            frameColor=(0, 0, 0, 0)
        )
        y -= 0.08
        
        for axis in ['x', 'y', 'z']:
            self.position_sliders[axis] = self._create_slider(
                self.frame, f"{axis.upper()}", y,
                range_=(-2, 2),
                command=self._on_position_change,
                extraArgs=[axis]
            )
            y -= 0.08
            
        y -= 0.05
        
        # Rotation Group
        DirectLabel(
            parent=self.frame,
            text="Rotation",
            scale=0.04,
            pos=(0, 0, y),
            text_fg=COLOR_LABEL,
            frameColor=(0, 0, 0, 0)
        )
        y -= 0.08
        
        for axis, label in [('h', 'Heading'), ('p', 'Pitch'), ('r', 'Roll')]:
            self.rotation_sliders[axis] = self._create_slider(
                self.frame, label, y,
                range_=(-180, 180),
                command=self._on_rotation_change,
                extraArgs=[axis]
            )
            y -= 0.08
            
        y -= 0.05
        
        # Scale Group
        DirectLabel(
            parent=self.frame,
            text="Dimensions",
            scale=0.04,
            pos=(0, 0, y),
            text_fg=COLOR_LABEL,
            frameColor=(0, 0, 0, 0)
        )
        y -= 0.08
        
        self.length_slider = self._create_slider(
            self.frame, "Length", y,
            range_=(0.1, 2.0),
            command=self._on_length_change
        )
        
    def _create_slider(self, parent, label, y, range_, command, extraArgs=None):
        """Helper to create a labelled slider."""
        DirectLabel(
            parent=parent,
            text=label,
            scale=0.03,
            pos=(-0.3, 0, y),
            text_align=TextNode.ALeft,
            text_fg=(0.7, 0.7, 0.7, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        slider = DirectSlider(
            parent=parent,
            range=range_,
            value=0,
            pageSize=(range_[1] - range_[0]) / 20,
            scale=0.15,
            pos=(0.1, 0, y),
            command=command,
            extraArgs=extraArgs if extraArgs else []
        )
        return slider

    def toggle(self):
        """Toggle visibility."""
        if self.visible:
            self.hide()
        else:
            self.show()
            
    def show(self):
        self.visible = True
        self.frame.show()
        self.toggle_btn['text'] = "▲ Precision Sliders"
        self._update_values() # Refresh values when opening
        
    def hide(self):
        self.visible = False
        self.frame.hide()
        self.toggle_btn['text'] = "▼ Precision Sliders"
        
    def update(self):
        """Update slider values from current selection."""
        # Only update if we are not the ones dragging the slider right now?
        # Actually DirectSlider updates its value, we need to update it if the model changed externally
        # e.g. via drag controller.
        self._update_values()

    def _update_values(self):
        """Sync sliders with selected bone."""
        if not self.visible:
            return
            
        bone_name = self.editor.selection.bone
        if not bone_name:
            return
            
        bone = self.editor.avatar.skeleton.get_bone(bone_name)
        if not bone:
            return
            
        pos = bone.local_transform.position
        self.position_sliders['x']['value'] = pos.x
        self.position_sliders['y']['value'] = pos.y
        self.position_sliders['z']['value'] = pos.z
        
        rot = bone.local_transform.rotation
        self.rotation_sliders['h']['value'] = rot.x
        self.rotation_sliders['p']['value'] = rot.y
        self.rotation_sliders['r']['value'] = rot.z
        
        if self.length_slider:
            self.length_slider['value'] = bone.length

    # Handlers
    def _on_position_change(self, axis: str):
        if not self.editor.selection or not self.editor.selection.bone:
            return
            
        bone_name = self.editor.selection.bone
        bone = self.editor.avatar.skeleton.get_bone(bone_name)
        if not bone:
            return
            
        new_val = self.position_sliders[axis]['value']
        old_pos = LVector3f(bone.local_transform.position)
        
        # Check if value actually changed to avoid spam? DirectSlider calls command often.
        if axis == 'x' and abs(old_pos.x - new_val) < 0.001: return
        if axis == 'y' and abs(old_pos.y - new_val) < 0.001: return
        if axis == 'z' and abs(old_pos.z - new_val) < 0.001: return

        # We need to use EditorCommand for Undo, but creating a command for every micro-slide is bad.
        # Ideally we'd have Start/End slide events. DirectGui doesn't easily give that.
        # For now we'll execute directly and maybe coalesce history?
        # Or just live with it/execute directly without history for now?
        # The original code generated history commands.
        
        def execute():
            b = self.editor.avatar.skeleton.get_bone(bone_name)
            if not b: return
            pos = b.local_transform.position
            if axis == 'x':
                b.local_transform.position = LVector3f(new_val, pos.y, pos.z)
            elif axis == 'y':
                b.local_transform.position = LVector3f(pos.x, new_val, pos.z)
            else:
                b.local_transform.position = LVector3f(pos.x, pos.y, new_val)
                
            # Symmetry
            if self.editor.symmetry_controller:
                self.editor.symmetry_controller.mirror_position(bone_name, b.local_transform.position)
                
            self.editor._rebuild_avatar() # Calling private method on editor, maybe expose public?
            
        def undo():
            b = self.editor.avatar.skeleton.get_bone(bone_name)
            if not b: return
            b.local_transform.position = old_pos
            
            # Symmetry
            if self.editor.symmetry_controller:
                self.editor.symmetry_controller.mirror_position(bone_name, old_pos)
                
            self.editor._rebuild_avatar()
            self._update_values()
            
        # Optimization: verify if we can skip history for continuous dragging if needed
        # For now, replicate original behavior
        cmd = EditorCommand(execute, undo, f"Move {bone_name}")
        self.editor.history.execute(cmd)

    def _on_rotation_change(self, axis: str):
        if not self.editor.selection or not self.editor.selection.bone:
            return
        
        bone_name = self.editor.selection.bone
        bone = self.editor.avatar.skeleton.get_bone(bone_name)
        if not bone: return
        
        new_val = self.rotation_sliders[axis]['value']
        old_rot = LVector3f(bone.local_transform.rotation)
        
        if axis == 'h' and abs(old_rot.x - new_val) < 0.001: return
        if axis == 'p' and abs(old_rot.y - new_val) < 0.001: return
        if axis == 'r' and abs(old_rot.z - new_val) < 0.001: return

        def execute():
            b = self.editor.avatar.skeleton.get_bone(bone_name)
            if not b: return
            rot = b.local_transform.rotation
            if axis == 'h':
                b.local_transform.rotation = LVector3f(new_val, rot.y, rot.z)
            elif axis == 'p':
                b.local_transform.rotation = LVector3f(rot.x, new_val, rot.z)
            else:
                b.local_transform.rotation = LVector3f(rot.x, rot.y, new_val)
                
            if self.editor.symmetry_controller:
                self.editor.symmetry_controller.mirror_rotation(bone_name, b.local_transform.rotation)
                
            self.editor._rebuild_avatar()
            
        def undo():
            b = self.editor.avatar.skeleton.get_bone(bone_name)
            if not b: return
            b.local_transform.rotation = old_rot
            
            if self.editor.symmetry_controller:
                self.editor.symmetry_controller.mirror_rotation(bone_name, old_rot)
                
            self.editor._rebuild_avatar()
            self._update_values()
            
        cmd = EditorCommand(execute, undo, f"Rotate {bone_name}")
        self.editor.history.execute(cmd)

    def _on_length_change(self):
        if not self.editor.selection or not self.editor.selection.bone:
            return
            
        bone_name = self.editor.selection.bone
        bone = self.editor.avatar.skeleton.get_bone(bone_name)
        if not bone: return
        
        new_len = self.length_slider['value']
        old_len = bone.length
        
        if abs(old_len - new_len) < 0.001: return
        
        def execute():
            b = self.editor.avatar.skeleton.get_bone(bone_name)
            if not b: return
            b.length = new_len
            
            if self.editor.symmetry_controller:
                self.editor.symmetry_controller.mirror_length(bone_name, new_len)
                
            self.editor._rebuild_avatar()
            
        def undo():
            b = self.editor.avatar.skeleton.get_bone(bone_name)
            if not b: return
            b.length = old_len
            
            if self.editor.symmetry_controller:
                self.editor.symmetry_controller.mirror_length(bone_name, old_len)
                
            self.editor._rebuild_avatar()
            self._update_values()
            
        cmd = EditorCommand(execute, undo, f"Scale {bone_name}")
        self.editor.history.execute(cmd)

