"""
Model Editor for visually editing VoxelAvatar skeletons.

Dev-level tool for correcting avatar modeling, rigging, and meshing issues.
"""
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DirectScrolledList,
    DirectSlider, DGG
)
from panda3d.core import NodePath, LVector3f
import math
from typing import Optional

from engine.ui.base_editor import BaseEditorWindow
from engine.ui.editors.voxel_canvas import VoxelCanvas
from engine.ui.editors.skeleton_renderer import SkeletonRenderer
from engine.ui.editors.editor_history import EditorHistory, EditorCommand
from engine.animation.voxel_avatar import VoxelAvatar
from engine.animation.skeleton import HumanoidSkeleton
from engine.core.logger import get_logger

logger = get_logger(__name__)


class ModelEditorWindow(BaseEditorWindow):
    """
    Editor for visually editing VoxelAvatar skeletons and bone properties.
    
    Features:
    - Skeleton wireframe visualization
    - Bone selection and highlighting
    - Transform editing (position, rotation, length, thickness)
    - Undo/redo history
    - Real-time avatar updates
    """
    
    def __init__(self, base):
        # Attribute initialization BEFORE super().__init__ which calls setup/hide
        self.canvas = None
        self.skeleton_renderer = None
        self.avatar = None
        self.history = EditorHistory(max_history=50)
        
        # Camera State
        self.cam_pivot = None
        self.saved_cam_parent = None
        self.saved_cam_transform = None
        self.orbit_distance = 5.0
        self.orbit_pitch = -20.0
        self.orbit_heading = 0.0
        self.is_orbiting = False
        
        # Selection State
        self.selected_bone: Optional[str] = None
        
        # UI Elements
        self.bone_list = None
        self.position_sliders = {}
        self.rotation_sliders = {}
        self.length_slider = None
        self.thickness_slider = None
        self.history_label = None
        self.undo_button = None
        self.redo_button = None
        
        self.update_task = None
        
        super().__init__(base, "Model Editor")
        
    def setup(self):
        """Initialize Model Editor UI and Canvas."""
        # Main frame container
        self.main_frame = DirectFrame(
            parent=self.ui_root,
            frameColor=(0, 0, 0, 0),
            frameSize=(-1.5, 1.5, -1.0, 1.0),
            pos=(0, 0, 0)
        )
        self.main_frame.hide()
        
        # Canvas for 3D visualization
        self.canvas = VoxelCanvas(self.base)
        self.canvas.root.reparentTo(self.base.render)
        self.canvas.root.hide()
        
        # Skeleton renderer
        self.skeleton_renderer = SkeletonRenderer(self.base.render)
        self.skeleton_renderer.set_visible(False)
        
        # Create default VoxelAvatar
        self._create_avatar()
        
        # UI Layout
        self._build_toolbar()
        self._build_bone_selector()
        self._build_transform_editor()
        self._build_history_controls()
        
    def _create_avatar(self):
        """Create a VoxelAvatar for editing."""
        skeleton = HumanoidSkeleton()
        self.avatar = VoxelAvatar(
            self.base.render,
            skeleton=skeleton,
            body_color=(0.2, 0.8, 0.2, 1.0),
            validate=True
        )
        self.avatar.root.hide()  # Hidden until editor shown
        
        # Update skeleton renderer
        self.skeleton_renderer.update_from_avatar(self.avatar)
        
    def show(self):
        """Enable editor mode."""
        super().show()
        
        # Show 3D content
        if self.avatar:
            self.avatar.root.show()
        self.skeleton_renderer.set_visible(True)
        
        # Setup camera
        self.saved_cam_parent = self.base.camera.getParent()
        self.saved_cam_transform = self.base.camera.getTransform()
        
        self.cam_pivot = self.base.render.attachNewNode("EditorCamPivot")
        self.cam_pivot.setPos(0, 0, 1.0)  # Focus on avatar center
        
        self.base.camera.reparentTo(self.cam_pivot)
        self.base.camera.setPos(0, -self.orbit_distance, 0)
        self.base.camera.lookAt(0, 0, 0)
        
        self._update_camera()
        
        # Input handlers
        self.accept("mouse3", self._start_orbit)
        self.accept("mouse3-up", self._stop_orbit)
        self.accept("wheel_up", self._zoom_in)
        self.accept("wheel_down", self._zoom_out)
        self.accept("control-z", self._on_undo)
        self.accept("control-shift-z", self._on_redo)
        
        # Update task
        self.update_task = self.base.taskMgr.add(self._update_editor, "ModelEditorUpdate")
        
    def hide(self):
        """Disable editor mode."""
        super().hide()
        
        # Hide 3D content
        if self.avatar:
            self.avatar.root.hide()
        self.skeleton_renderer.set_visible(False)
        
        # Restore camera
        if self.saved_cam_parent:
            self.base.camera.reparentTo(self.saved_cam_parent)
            self.base.camera.setTransform(self.saved_cam_transform)
            
        if self.cam_pivot:
            self.cam_pivot.removeNode()
            self.cam_pivot = None
            
        # Cleanup inputs
        self.ignore("mouse3")
        self.ignore("mouse3-up")
        self.ignore("wheel_up")
        self.ignore("wheel_down")
        self.ignore("control-z")
        self.ignore("control-shift-z")
        
        if self.update_task:
            self.base.taskMgr.remove(self.update_task)
            self.update_task = None
            
    # Camera Controls
    
    def _update_editor(self, task):
        """Frame update for camera and interaction."""
        if self.is_orbiting:
            md = self.base.win.getPointer(0)
            x = md.getX()
            y = md.getY()
            
            if hasattr(self, 'last_mouse_x'):
                dx = x - self.last_mouse_x
                dy = y - self.last_mouse_y
                
                self.orbit_heading -= dx * 0.5
                self.orbit_pitch = min(max(self.orbit_pitch - dy * 0.5, -89), 89)
                self._update_camera()
                
            self.last_mouse_x = x
            self.last_mouse_y = y
            
        return task.cont
        
    def _start_orbit(self):
        self.is_orbiting = True
        md = self.base.win.getPointer(0)
        self.last_mouse_x = md.getX()
        self.last_mouse_y = md.getY()
        
    def _stop_orbit(self):
        self.is_orbiting = False
        
    def _zoom_in(self):
        self.orbit_distance = max(2.0, self.orbit_distance - 0.5)
        self._update_camera()
        
    def _zoom_out(self):
        self.orbit_distance = min(20.0, self.orbit_distance + 0.5)
        self._update_camera()

    def _update_camera(self):
        if not self.cam_pivot:
            return
        self.cam_pivot.setHpr(self.orbit_heading, self.orbit_pitch, 0)
        self.base.camera.setPos(0, -self.orbit_distance, 0)

    # UI Construction
    
    def _build_toolbar(self):
        """Top toolbar with title and history controls."""
        frame = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-1.3, 1.3, 0.85, 0.95),
            pos=(0, 0, 0)
        )
        
        DirectLabel(
            parent=frame,
            text="Model Editor",
            scale=0.04,
            pos=(-1.1, 0, 0.88),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        # History status
        self.history_label = DirectLabel(
            parent=frame,
            text="0 actions",
            scale=0.03,
            pos=(0, 0, 0.88),
            text_fg=(0.7, 0.7, 0.7, 1),
            frameColor=(0, 0, 0, 0)
        )
        
    def _build_bone_selector(self):
        """Left sidebar with bone selection tree."""
        frame = self._create_panel((-1.3, -0.85, -0.9, 0.8), "Bones")
        
        # Bone list (simplified - full tree view would be more complex)
        if self.avatar:
            bone_names = list(self.avatar.skeleton.bones.keys())
            
            # Create scrolled list
            y_pos = 0.65
            for bone_name in bone_names:
                btn = DirectButton(
                    parent=frame,
                    text=bone_name,
                    scale=0.035,
                    pos=(-1.05, 0, y_pos),
                    frameColor=(0.2, 0.2, 0.2, 1),
                    text_fg=(1, 1, 1, 1),
                    text_align=0,  # Left align
                    command=self._select_bone,
                    extraArgs=[bone_name]
                )
                y_pos -= 0.06
                
                if y_pos < -0.8:
                    break  # TODO: Implement scrolling
                    
    def _build_transform_editor(self):
        """Right sidebar with transform sliders."""
        frame = self._create_panel((0.85, 1.3, -0.9, 0.8), "Transform")
        
        y = 0.65
        
        # Position sliders
        DirectLabel(parent=frame, text="Position", scale=0.04, pos=(1.05, 0, y), 
                   text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0))
        y -= 0.08
        
        for axis in ['X', 'Y', 'Z']:
            DirectLabel(parent=frame, text=axis, scale=0.03, pos=(0.9, 0, y),
                       text_fg=(0.8, 0.8, 0.8, 1), frameColor=(0, 0, 0, 0))
            
            slider = DirectSlider(
                parent=frame,
                range=(-2.0, 2.0),
                value=0.0,
                pageSize=0.1,
                scale=0.3,
                pos=(1.15, 0, y),
                command=self._on_position_changed,
                extraArgs=[axis.lower()]
            )
            self.position_sliders[axis.lower()] = slider
            y -= 0.06
            
        y -= 0.04
        
        # Rotation sliders
        DirectLabel(parent=frame, text="Rotation", scale=0.04, pos=(1.05, 0, y),
                   text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0))
        y -= 0.08
        
        for axis in ['H', 'P', 'R']:
            DirectLabel(parent=frame, text=axis, scale=0.03, pos=(0.9, 0, y),
                       text_fg=(0.8, 0.8, 0.8, 1), frameColor=(0, 0, 0, 0))
            
            slider = DirectSlider(
                parent=frame,
                range=(-180, 180),
                value=0.0,
                pageSize=10,
                scale=0.3,
                pos=(1.15, 0, y),
                command=self._on_rotation_changed,
                extraArgs=[axis.lower()]
            )
            self.rotation_sliders[axis.lower()] = slider
            y -= 0.06
            
        y -= 0.04
        
        # Length slider
        DirectLabel(parent=frame, text="Length", scale=0.04, pos=(1.05, 0, y),
                   text_fg=(1, 1, 1, 1), frameColor=(0, 0, 0, 0))
        y -= 0.06
        
        self.length_slider = DirectSlider(
            parent=frame,
            range=(0.05, 1.0),
            value=0.3,
            pageSize=0.05,
            scale=0.3,
            pos=(1.15, 0, y),
            command=self._on_length_changed
        )
        
    def _build_history_controls(self):
        """Bottom bar with undo/redo buttons."""
        frame = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.3, 0.3, -0.95, -0.85),
            pos=(0, 0, 0)
        )
        
        self.undo_button = DirectButton(
            parent=frame,
            text="Undo (Ctrl+Z)",
            scale=0.04,
            pos=(-0.15, 0, -0.9),
            frameColor=(0.3, 0.3, 0.3, 1),
            text_fg=(1, 1, 1, 1),
            command=self._on_undo
        )
        
        self.redo_button = DirectButton(
            parent=frame,
            text="Redo (Ctrl+Shift+Z)",
            scale=0.04,
            pos=(0.15, 0, -0.9),
            frameColor=(0.3, 0.3, 0.3, 1),
            text_fg=(1, 1, 1, 1),
            command=self._on_redo
        )
        
        self._update_history_ui()
        
    def _create_panel(self, frame_size, title):
        """Helper to create standard side panel."""
        frame = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.12, 0.12, 0.12, 0.95),
            frameSize=frame_size,
            pos=(0, 0, 0),
            relief=DGG.FLAT
        )
        
        DirectLabel(
            parent=frame,
            text=title,
            scale=0.05,
            pos=(frame_size[0] + 0.15, 0, frame_size[3] - 0.05),
            text_fg=(0.8, 0.8, 0.8, 1),
            frameColor=(0, 0, 0, 0)
        )
        return frame
        
    # Bone Selection
    
    def _select_bone(self, bone_name: str):
        """Select a bone for editing."""
        self.selected_bone = bone_name
        self.skeleton_renderer.highlight_bone(bone_name)
        self._update_transform_ui()
        logger.debug(f"Selected bone: {bone_name}")
        
    def _update_transform_ui(self):
        """Update transform sliders to match selected bone."""
        if not self.selected_bone or not self.avatar:
            return
            
        bone = self.avatar.skeleton.get_bone(self.selected_bone)
        if not bone:
            return
            
        # Update position sliders
        pos = bone.local_transform.position
        self.position_sliders['x']['value'] = pos.x
        self.position_sliders['y']['value'] = pos.y
        self.position_sliders['z']['value'] = pos.z
        
        # Update rotation sliders
        rot = bone.local_transform.rotation
        self.rotation_sliders['h']['value'] = rot.x
        self.rotation_sliders['p']['value'] = rot.y
        self.rotation_sliders['r']['value'] = rot.z
        
        # Update length slider
        if self.length_slider:
            self.length_slider['value'] = bone.length
            
    # Transform Editing
    
    def _on_position_changed(self, axis: str):
        """Handle position slider change."""
        if not self.selected_bone:
            return
            
        bone = self.avatar.skeleton.get_bone(self.selected_bone)
        if not bone:
            return
            
        new_value = self.position_sliders[axis]['value']
        old_pos = LVector3f(bone.local_transform.position)
        
        # Create command
        def execute():
            pos = bone.local_transform.position
            if axis == 'x':
                bone.local_transform.position = LVector3f(new_value, pos.y, pos.z)
            elif axis == 'y':
                bone.local_transform.position = LVector3f(pos.x, new_value, pos.z)
            elif axis == 'z':
                bone.local_transform.position = LVector3f(pos.x, pos.y, new_value)
            self._rebuild_avatar()
            
        def undo():
            bone.local_transform.position = old_pos
            self._rebuild_avatar()
            self._update_transform_ui()
            
        cmd = EditorCommand(execute, undo, f"Move {self.selected_bone} {axis.upper()}")
        self.history.execute(cmd)
        self._update_history_ui()
        
    def _on_rotation_changed(self, axis: str):
        """Handle rotation slider change."""
        if not self.selected_bone:
            return
            
        bone = self.avatar.skeleton.get_bone(self.selected_bone)
        if not bone:
            return
            
        new_value = self.rotation_sliders[axis]['value']
        old_rot = LVector3f(bone.local_transform.rotation)
        
        def execute():
            rot = bone.local_transform.rotation
            if axis == 'h':
                bone.local_transform.rotation = LVector3f(new_value, rot.y, rot.z)
            elif axis == 'p':
                bone.local_transform.rotation = LVector3f(rot.x, new_value, rot.z)
            elif axis == 'r':
                bone.local_transform.rotation = LVector3f(rot.x, rot.y, new_value)
            self._rebuild_avatar()
            
        def undo():
            bone.local_transform.rotation = old_rot
            self._rebuild_avatar()
            self._update_transform_ui()
            
        cmd = EditorCommand(execute, undo, f"Rotate {self.selected_bone} {axis.upper()}")
        self.history.execute(cmd)
        self._update_history_ui()
        
    def _on_length_changed(self):
        """Handle length slider change."""
        if not self.selected_bone or not self.length_slider:
            return
            
        bone = self.avatar.skeleton.get_bone(self.selected_bone)
        if not bone:
            return
            
        new_length = self.length_slider['value']
        old_length = bone.length
        
        def execute():
            bone.length = new_length
            self._rebuild_avatar()
            
        def undo():
            bone.length = old_length
            self._rebuild_avatar()
            self._update_transform_ui()
            
        cmd = EditorCommand(execute, undo, f"Resize {self.selected_bone}")
        self.history.execute(cmd)
        self._update_history_ui()
        
    def _rebuild_avatar(self):
        """Rebuild avatar visuals after bone modification."""
        if not self.avatar:
            return
            
        # Remove old avatar
        old_pos = self.avatar.root.getPos()
        self.avatar.cleanup()
        
        # Create new avatar with modified skeleton
        self.avatar = VoxelAvatar(
            self.base.render,
            skeleton=self.avatar.skeleton,  # Reuse modified skeleton
            body_color=(0.2, 0.8, 0.2, 1.0),
            validate=False  # Skip validation during editing
        )
        self.avatar.root.setPos(old_pos)
        
        # Update skeleton renderer
        self.skeleton_renderer.update_from_avatar(self.avatar)
        if self.selected_bone:
            self.skeleton_renderer.highlight_bone(self.selected_bone)
            
    # History Management
    
    def _on_undo(self):
        """Handle undo button/shortcut."""
        if self.history.undo():
            self._update_history_ui()
            logger.debug("Undo successful")
            
    def _on_redo(self):
        """Handle redo button/shortcut."""
        if self.history.redo():
            self._update_history_ui()
            logger.debug("Redo successful")
            
    def _update_history_ui(self):
        """Update history UI elements."""
        if self.history_label:
            count = self.history.get_history_count()
            self.history_label['text'] = f"{count} action{'s' if count != 1 else ''}"
            
        if self.undo_button:
            if self.history.can_undo():
                self.undo_button['frameColor'] = (0.3, 0.5, 0.3, 1)
            else:
                self.undo_button['frameColor'] = (0.2, 0.2, 0.2, 1)
                
        if self.redo_button:
            if self.history.can_redo():
                self.redo_button['frameColor'] = (0.3, 0.5, 0.3, 1)
            else:
                self.redo_button['frameColor'] = (0.2, 0.2, 0.2, 1)
                
    def cleanup(self):
        """Clean up resources."""
        self.hide()
        
        if self.avatar:
            self.avatar.cleanup()
            
        if self.skeleton_renderer:
            self.skeleton_renderer.cleanup()
            
        if self.canvas:
            self.canvas.cleanup()
            
        super().cleanup()
