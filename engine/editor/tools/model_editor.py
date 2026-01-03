"""
ModelEditor: Standalone editor for VoxelAvatar skeleton editing.

Part of the standalone editor suite - works without game runtime.

Features Spore-inspired mouse-controlled transformations:
- Click to select bones in 3D viewport
- Drag to move/rotate/scale
- Inline contextual hints for learning
"""

from typing import Optional
from panda3d.core import NodePath, LVector3f, TextNode, Point2
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DirectSlider, DGG
)

from engine.editor.tools.common.orbit_camera import OrbitCamera
from engine.editor.tools.common.skeleton_renderer import SkeletonRenderer
from engine.editor.tools.common.editor_history import EditorHistory, EditorCommand
from engine.editor.tools.common.bone_picker import BonePicker
from engine.editor.tools.common.drag_controller import DragController, DragMode
from engine.editor.selection import EditorSelection
from engine.animation.voxel_avatar import VoxelAvatar
from engine.animation.skeleton import HumanoidSkeleton
from engine.core.logger import get_logger

logger = get_logger(__name__)


# Human-readable bone names for non-technical users
BONE_DISPLAY_NAMES = {
    "hips": "Hips", "spine": "Spine", "chest": "Chest", "head": "Head",
    "shoulder_left": "L Shoulder", "shoulder_right": "R Shoulder",
    "upper_arm_left": "L Upper Arm", "upper_arm_right": "R Upper Arm",
    "forearm_left": "L Forearm", "forearm_right": "R Forearm",
    "hand_left": "L Hand", "hand_right": "R Hand",
    "thigh_left": "L Thigh", "thigh_right": "R Thigh",
    "shin_left": "L Shin", "shin_right": "R Shin",
    "foot_left": "L Foot", "foot_right": "R Foot",
}

# Theme Colors
COLOR_PANEL_BG = (0.12, 0.12, 0.14, 0.95)
COLOR_HEADER_BG = (0.18, 0.18, 0.20, 1.0)
COLOR_BUTTON = (0.22, 0.22, 0.26, 1)
COLOR_BUTTON_ACTIVE = (0.3, 0.5, 0.3, 1)
COLOR_HINT_BG = (0.1, 0.1, 0.1, 0.8)


class ModelEditor:
    """Editor for visually editing VoxelAvatar skeletons.
    
    Features:
    - Click-to-select bones in 3D viewport
    - Drag-to-transform (move/rotate/scale)
    - Inline contextual hints
    - Hidden sliders (expandable for precision)
    - Undo/redo with keyboard shortcuts
    """
    
    def __init__(self, app):
        """Initialize model editor.
        
        Args:
            app: EditorApp instance
        """
        self.app = app
        self.visible = False
        
        # Shared selection
        self.selection: Optional[EditorSelection] = None
        
        # History
        self.history = EditorHistory(max_history=50)
        
        # Camera
        self.orbit_camera = OrbitCamera(app, focus_pos=(0, 0, 1))
        
        # 3D content
        self.avatar: Optional[VoxelAvatar] = None
        self.skeleton_renderer: Optional[SkeletonRenderer] = None
        
        # Mouse interaction
        self.bone_picker: Optional[BonePicker] = None
        self.drag_controller: Optional[DragController] = None
        self.current_mode = DragMode.MOVE
        
        # UI
        self.main_frame: Optional[DirectFrame] = None
        self.hint_label: Optional[DirectLabel] = None
        self.status_label: Optional[DirectLabel] = None
        self.mode_buttons = {}
        self.sliders_visible = False
        self.slider_panel: Optional[DirectFrame] = None
        self.position_sliders = {}
        self.rotation_sliders = {}
        self.length_slider = None
        
        # Update task
        self.update_task = None
        
        # Build (hidden initially)
        self._setup()
        self.hide()
        
    def set_selection(self, selection: EditorSelection):
        """Set shared selection state."""
        self.selection = selection
        self.selection.add_observer(self._on_selection_changed)
        
    def _on_selection_changed(self, prop: str, value):
        """Handle shared selection changes."""
        if prop == "bone":
            self._update_hint()
            self._update_sliders()
            if self.skeleton_renderer:
                self.skeleton_renderer.highlight_bone(value)
                
    def _setup(self):
        """Initialize editor UI and 3D content."""
        # Main frame
        self.main_frame = DirectFrame(
            parent=self.app.aspect2d,
            frameColor=(0, 0, 0, 0),
            frameSize=(-1.0, 1.4, -1.0, 1.0),
            pos=(0.0, 0, 0)
        )
        
        # 3D content
        self._create_avatar()
        self.skeleton_renderer = SkeletonRenderer(self.app.render)
        self.skeleton_renderer.update_from_avatar(self.avatar)
        
        # Mouse interaction
        self.bone_picker = BonePicker(self.app, self.app.render)
        self.bone_picker.setup_skeleton(self.avatar.skeleton, self.avatar.bone_nodes)
        self.bone_picker.on_bone_selected = self._on_bone_clicked
        self.bone_picker.on_bone_hovered = self._on_bone_hovered
        
        self.drag_controller = DragController(
            self.app, 
            self.avatar.skeleton, 
            self.avatar.bone_nodes
        )
        self.drag_controller.on_transform_changed = self._on_transform_changed
        
        # Build UI
        self._build_toolbar()
        self._build_bone_panel()
        self._build_slider_panel()  # Hidden by default
        self._build_hint_bar()
        
    def _create_avatar(self):
        """Create VoxelAvatar for editing."""
        skeleton = HumanoidSkeleton()
        self.avatar = VoxelAvatar(
            self.app.render,
            skeleton=skeleton,
            body_color=(0.2, 0.8, 0.2, 1.0),
            validate=True
        )
        self.avatar.root.hide()
        
    # ─────────────────────────────────────────────────────────────────
    # UI Construction
    # ─────────────────────────────────────────────────────────────────
    
    def _build_toolbar(self):
        """Build top toolbar with mode buttons."""
        toolbar = DirectFrame(
            parent=self.main_frame,
            frameColor=COLOR_HEADER_BG,
            frameSize=(-0.65, 0.95, 0.85, 0.98),
            pos=(0, 0, 0)
        )
        
        DirectLabel(
            parent=toolbar,
            text="Model Editor",
            scale=0.04,
            pos=(0.15, 0, 0.90),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        # Mode buttons
        modes = [
            ("Move", DragMode.MOVE, "G"),
            ("Rotate", DragMode.ROTATE, "R"),
            ("Scale", DragMode.SCALE, "S"),
        ]
        
        x_pos = 0.50
        for label, mode, hotkey in modes:
            btn = DirectButton(
                parent=toolbar,
                text=f"{label} [{hotkey}]",
                scale=0.028,
                pos=(x_pos, 0, 0.90),
                frameColor=COLOR_BUTTON_ACTIVE if mode == self.current_mode else COLOR_BUTTON,
                text_fg=(1, 1, 1, 1),
                command=self._set_mode,
                extraArgs=[mode]
            )
            self.mode_buttons[mode] = btn
            x_pos += 0.15
            
        # Undo/Redo
        DirectButton(
            parent=toolbar,
            text="Undo",
            scale=0.025,
            pos=(-0.55, 0, 0.90),
            frameColor=COLOR_BUTTON,
            text_fg=(1, 1, 1, 1),
            command=self._on_undo
        )
        DirectButton(
            parent=toolbar,
            text="Redo",
            scale=0.025,
            pos=(-0.42, 0, 0.90),
            frameColor=COLOR_BUTTON,
            text_fg=(1, 1, 1, 1),
            command=self._on_redo
        )
        
    def _build_bone_panel(self):
        """Build left panel with bone list."""
        panel = DirectFrame(
            parent=self.main_frame,
            frameColor=COLOR_PANEL_BG,
            frameSize=(-1.0, -0.65, -0.85, 0.80),
            pos=(0, 0, 0)
        )
        
        DirectLabel(
            parent=panel,
            text="Bones",
            scale=0.04,
            pos=(-0.825, 0, 0.72),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        # Bone buttons (scrollable list)
        if self.avatar:
            y_pos = 0.62
            for bone_name in self.avatar.skeleton.bones.keys():
                display = BONE_DISPLAY_NAMES.get(bone_name, bone_name.replace('_', ' ').title())
                DirectButton(
                    parent=panel,
                    text=display,
                    scale=0.022,
                    pos=(-0.82, 0, y_pos),
                    frameColor=COLOR_BUTTON,
                    text_fg=(1, 1, 1, 1),
                    text_align=TextNode.ALeft,
                    command=self._select_bone,
                    extraArgs=[bone_name]
                )
                y_pos -= 0.04
                if y_pos < -0.75:
                    break
                    
        # Show Sliders toggle
        DirectButton(
            parent=panel,
            text="▼ Precision Sliders",
            scale=0.025,
            pos=(-0.825, 0, -0.78),
            frameColor=(0.25, 0.25, 0.28, 1),
            text_fg=(0.7, 0.7, 0.7, 1),
            command=self._toggle_sliders
        )
        
    def _build_slider_panel(self):
        """Build collapsible precision slider panel (hidden by default)."""
        self.slider_panel = DirectFrame(
            parent=self.main_frame,
            frameColor=COLOR_PANEL_BG,
            frameSize=(0.95, 1.35, -0.85, 0.80),
            pos=(0, 0, 0)
        )
        
        DirectLabel(
            parent=self.slider_panel,
            text="Precision Controls",
            scale=0.035,
            pos=(1.15, 0, 0.72),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        y = 0.60
        
        # Position sliders
        DirectLabel(parent=self.slider_panel, text="Position", scale=0.028, 
                   pos=(1.15, 0, y), text_fg=(0.8, 0.8, 0.8, 1), frameColor=(0,0,0,0))
        y -= 0.05
        
        for axis, label in [('x', 'X'), ('y', 'Y'), ('z', 'Z')]:
            DirectLabel(parent=self.slider_panel, text=label, scale=0.02,
                       pos=(1.0, 0, y), text_fg=(0.6, 0.6, 0.6, 1), frameColor=(0,0,0,0))
            slider = DirectSlider(
                parent=self.slider_panel,
                range=(-2, 2), value=0, pageSize=0.1,
                scale=0.12, pos=(1.18, 0, y),
                command=self._on_position_slider,
                extraArgs=[axis]
            )
            self.position_sliders[axis] = slider
            y -= 0.04
            
        y -= 0.03
        
        # Rotation sliders
        DirectLabel(parent=self.slider_panel, text="Rotation", scale=0.028,
                   pos=(1.15, 0, y), text_fg=(0.8, 0.8, 0.8, 1), frameColor=(0,0,0,0))
        y -= 0.05
        
        for axis, label in [('h', 'H'), ('p', 'P'), ('r', 'R')]:
            DirectLabel(parent=self.slider_panel, text=label, scale=0.02,
                       pos=(1.0, 0, y), text_fg=(0.6, 0.6, 0.6, 1), frameColor=(0,0,0,0))
            slider = DirectSlider(
                parent=self.slider_panel,
                range=(-180, 180), value=0, pageSize=10,
                scale=0.12, pos=(1.18, 0, y),
                command=self._on_rotation_slider,
                extraArgs=[axis]
            )
            self.rotation_sliders[axis] = slider
            y -= 0.04
            
        y -= 0.03
        
        # Length slider
        DirectLabel(parent=self.slider_panel, text="Length", scale=0.028,
                   pos=(1.15, 0, y), text_fg=(0.8, 0.8, 0.8, 1), frameColor=(0,0,0,0))
        y -= 0.05
        
        self.length_slider = DirectSlider(
            parent=self.slider_panel,
            range=(0.05, 1.0), value=0.3, pageSize=0.05,
            scale=0.12, pos=(1.15, 0, y),
            command=self._on_length_slider
        )
        
        # Start hidden
        self.slider_panel.hide()
        
    def _build_hint_bar(self):
        """Build contextual hint bar at bottom."""
        hint_frame = DirectFrame(
            parent=self.main_frame,
            frameColor=COLOR_HINT_BG,
            frameSize=(-0.65, 0.95, -0.98, -0.88),
            pos=(0, 0, 0)
        )
        
        self.hint_label = DirectLabel(
            parent=hint_frame,
            text="Click a bone to select it",
            scale=0.03,
            pos=(0.15, 0, -0.93),
            text_fg=(0.8, 0.8, 0.8, 1),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0)
        )
        
        self.status_label = DirectLabel(
            parent=hint_frame,
            text="",
            scale=0.025,
            pos=(0.8, 0, -0.93),
            text_fg=(0.5, 0.5, 0.5, 1),
            frameColor=(0, 0, 0, 0)
        )
        
    # ─────────────────────────────────────────────────────────────────
    # Mouse Interaction
    # ─────────────────────────────────────────────────────────────────
    
    def _on_bone_clicked(self, bone_name: str):
        """Handle bone selection from 3D click."""
        if self.selection:
            self.selection.bone = bone_name
        self._update_hint()
        
    def _on_bone_hovered(self, bone_name: Optional[str]):
        """Handle bone hover for visual feedback."""
        if bone_name and not self.drag_controller.is_dragging():
            self._set_hint(f"Click to select: {BONE_DISPLAY_NAMES.get(bone_name, bone_name)}")
        elif not self.drag_controller.is_dragging():
            self._update_hint()
            
    def _on_mouse_press(self):
        """Handle mouse button press for drag start."""
        if not self.visible:
            return
            
        # Check if we're over a bone
        if not self.app.mouseWatcherNode.hasMouse():
            return
            
        mpos = self.app.mouseWatcherNode.getMouse()
        mouse_pos = Point2(mpos.x, mpos.y)
        
        # First, try to pick a bone
        bone = self.bone_picker.pick(mouse_pos)
        
        if bone:
            # Select it
            if self.selection:
                self.selection.bone = bone
                
            # Start drag
            self.drag_controller.begin_drag(bone, self.current_mode, mouse_pos)
            self._set_hint(f"Dragging {BONE_DISPLAY_NAMES.get(bone, bone)}...")
            
    def _on_mouse_release(self):
        """Handle mouse button release for drag end."""
        if self.drag_controller.is_dragging():
            self.drag_controller.end_drag(self.history)
            self._rebuild_avatar()
            self._update_hint()
            
    def _on_mouse_move(self):
        """Handle mouse movement during drag."""
        if not self.app.mouseWatcherNode.hasMouse():
            return
            
        mpos = self.app.mouseWatcherNode.getMouse()
        mouse_pos = Point2(mpos.x, mpos.y)
        
        if self.drag_controller.is_dragging():
            self.drag_controller.update_drag(mouse_pos)
        else:
            self.bone_picker.update_hover(mouse_pos)
            
    def _on_scroll(self, direction: int):
        """Handle scroll wheel for scaling selected bone."""
        if not self.selection or not self.selection.bone:
            return
            
        bone = self.avatar.skeleton.get_bone(self.selection.bone)
        if not bone:
            return
            
        # Scale by scroll amount
        delta = direction * 0.05
        old_length = bone.length
        new_length = max(0.05, bone.length + delta)
        bone_name = self.selection.bone
        
        def execute():
            b = self.avatar.skeleton.get_bone(bone_name)
            if b:
                b.length = new_length
                
        def undo():
            b = self.avatar.skeleton.get_bone(bone_name)
            if b:
                b.length = old_length
                
        cmd = EditorCommand(execute, undo, f"Scale {bone_name}")
        self.history.execute(cmd)
        self._rebuild_avatar()
        self._set_hint(f"Scaled {BONE_DISPLAY_NAMES.get(bone_name, bone_name)}")
        
    def _on_transform_changed(self):
        """Handle real-time transform update during drag."""
        self._rebuild_avatar()
        
    # ─────────────────────────────────────────────────────────────────
    # Mode & Selection
    # ─────────────────────────────────────────────────────────────────
    
    def _set_mode(self, mode: DragMode):
        """Set current transform mode."""
        self.current_mode = mode
        
        # Update button styles
        for m, btn in self.mode_buttons.items():
            btn['frameColor'] = COLOR_BUTTON_ACTIVE if m == mode else COLOR_BUTTON
            
        self._update_hint()
        
    def _select_bone(self, bone_name: str):
        """Select bone from UI list."""
        if self.selection:
            self.selection.bone = bone_name
        if self.skeleton_renderer:
            self.skeleton_renderer.highlight_bone(bone_name)
        self._update_hint()
        self._update_sliders()
        
    def _toggle_sliders(self):
        """Toggle visibility of precision slider panel."""
        self.sliders_visible = not self.sliders_visible
        if self.sliders_visible:
            self.slider_panel.show()
        else:
            self.slider_panel.hide()
            
    # ─────────────────────────────────────────────────────────────────
    # Hints & Feedback
    # ─────────────────────────────────────────────────────────────────
    
    def _set_hint(self, text: str):
        """Set hint bar text."""
        if self.hint_label:
            self.hint_label['text'] = text
            
    def _update_hint(self):
        """Update hint based on current state."""
        if not self.selection or not self.selection.bone:
            self._set_hint("Click a bone to select it")
        else:
            bone_name = BONE_DISPLAY_NAMES.get(self.selection.bone, self.selection.bone)
            mode_name = self.current_mode.value.title()
            self._set_hint(f"Selected: {bone_name} | Drag to {mode_name} | Scroll to Scale")
            
        # Update status
        if self.status_label:
            count = self.history.get_history_count()
            self.status_label['text'] = f"{count} edit{'s' if count != 1 else ''}"
            
    # ─────────────────────────────────────────────────────────────────
    # Slider Handlers (precision mode)
    # ─────────────────────────────────────────────────────────────────
    
    def _update_sliders(self):
        """Sync sliders with selected bone."""
        if not self.selection or not self.selection.bone:
            return
            
        bone = self.avatar.skeleton.get_bone(self.selection.bone)
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
            
    def _on_position_slider(self, axis: str):
        """Handle position slider change."""
        if not self.selection or not self.selection.bone:
            return
            
        bone = self.avatar.skeleton.get_bone(self.selection.bone)
        if not bone:
            return
            
        new_val = self.position_sliders[axis]['value']
        old_pos = LVector3f(bone.local_transform.position)
        bone_name = self.selection.bone
        
        def execute():
            b = self.avatar.skeleton.get_bone(bone_name)
            pos = b.local_transform.position
            if axis == 'x':
                b.local_transform.position = LVector3f(new_val, pos.y, pos.z)
            elif axis == 'y':
                b.local_transform.position = LVector3f(pos.x, new_val, pos.z)
            else:
                b.local_transform.position = LVector3f(pos.x, pos.y, new_val)
            self._rebuild_avatar()
            
        def undo():
            b = self.avatar.skeleton.get_bone(bone_name)
            b.local_transform.position = old_pos
            self._rebuild_avatar()
            self._update_sliders()
            
        cmd = EditorCommand(execute, undo, f"Move {bone_name}")
        self.history.execute(cmd)
        
    def _on_rotation_slider(self, axis: str):
        """Handle rotation slider change."""
        if not self.selection or not self.selection.bone:
            return
            
        bone = self.avatar.skeleton.get_bone(self.selection.bone)
        if not bone:
            return
            
        new_val = self.rotation_sliders[axis]['value']
        old_rot = LVector3f(bone.local_transform.rotation)
        bone_name = self.selection.bone
        
        def execute():
            b = self.avatar.skeleton.get_bone(bone_name)
            rot = b.local_transform.rotation
            if axis == 'h':
                b.local_transform.rotation = LVector3f(new_val, rot.y, rot.z)
            elif axis == 'p':
                b.local_transform.rotation = LVector3f(rot.x, new_val, rot.z)
            else:
                b.local_transform.rotation = LVector3f(rot.x, rot.y, new_val)
            self._rebuild_avatar()
            
        def undo():
            b = self.avatar.skeleton.get_bone(bone_name)
            b.local_transform.rotation = old_rot
            self._rebuild_avatar()
            self._update_sliders()
            
        cmd = EditorCommand(execute, undo, f"Rotate {bone_name}")
        self.history.execute(cmd)
        
    def _on_length_slider(self):
        """Handle length slider change."""
        if not self.selection or not self.selection.bone:
            return
            
        bone = self.avatar.skeleton.get_bone(self.selection.bone)
        if not bone:
            return
            
        new_len = self.length_slider['value']
        old_len = bone.length
        bone_name = self.selection.bone
        
        def execute():
            b = self.avatar.skeleton.get_bone(bone_name)
            b.length = new_len
            self._rebuild_avatar()
            
        def undo():
            b = self.avatar.skeleton.get_bone(bone_name)
            b.length = old_len
            self._rebuild_avatar()
            self._update_sliders()
            
        cmd = EditorCommand(execute, undo, f"Scale {bone_name}")
        self.history.execute(cmd)
        
    # ─────────────────────────────────────────────────────────────────
    # Avatar Management
    # ─────────────────────────────────────────────────────────────────
    
    def _rebuild_avatar(self):
        """Rebuild avatar after skeleton changes."""
        if not self.avatar:
            return
            
        skeleton = self.avatar.skeleton
        self.avatar.cleanup()
        
        self.avatar = VoxelAvatar(
            self.app.render,
            skeleton=skeleton,
            body_color=(0.2, 0.8, 0.2, 1.0),
            validate=False
        )
        
        # Update dependent systems
        if self.skeleton_renderer:
            self.skeleton_renderer.update_from_avatar(self.avatar)
            if self.selection and self.selection.bone:
                self.skeleton_renderer.highlight_bone(self.selection.bone)
                
        if self.bone_picker:
            self.bone_picker.setup_skeleton(self.avatar.skeleton, self.avatar.bone_nodes)
            
        if self.drag_controller:
            self.drag_controller.set_skeleton(self.avatar.skeleton, self.avatar.bone_nodes)
            
    # ─────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────
    
    def show(self):
        """Show the editor."""
        self.visible = True
        
        if self.main_frame:
            self.main_frame.show()
        if self.avatar:
            self.avatar.root.show()
        if self.skeleton_renderer:
            self.skeleton_renderer.set_visible(True)
            
        self.orbit_camera.enable()
        
        # Keyboard shortcuts
        self.app.accept("control-z", self._on_undo)
        self.app.accept("control-shift-z", self._on_redo)
        self.app.accept("g", self._set_mode, [DragMode.MOVE])
        self.app.accept("r", self._set_mode, [DragMode.ROTATE])
        self.app.accept("s", self._set_mode, [DragMode.SCALE])
        self.app.accept("escape", self._cancel_drag)
        
        # Mouse controls
        self.app.accept("mouse1", self._on_mouse_press)
        self.app.accept("mouse1-up", self._on_mouse_release)
        self.app.accept("wheel_up", self._on_scroll, [1])
        self.app.accept("wheel_down", self._on_scroll, [-1])
        
        # Start update loop
        self.update_task = self.app.taskMgr.add(self._update, "ModelEditorUpdate")
        
        logger.debug("ModelEditor shown")
        
    def hide(self):
        """Hide the editor."""
        self.visible = False
        
        if self.main_frame:
            self.main_frame.hide()
        if self.avatar:
            self.avatar.root.hide()
        if self.skeleton_renderer:
            self.skeleton_renderer.set_visible(False)
            
        self.orbit_camera.disable()
        
        # Remove bindings
        self.app.ignore("control-z")
        self.app.ignore("control-shift-z")
        self.app.ignore("g")
        self.app.ignore("r")
        self.app.ignore("s")
        self.app.ignore("escape")
        self.app.ignore("mouse1")
        self.app.ignore("mouse1-up")
        self.app.ignore("wheel_up")
        self.app.ignore("wheel_down")
        
        if self.update_task:
            self.app.taskMgr.remove(self.update_task)
            self.update_task = None
            
        logger.debug("ModelEditor hidden")
        
    def _update(self, task):
        """Per-frame update."""
        self.orbit_camera.update()
        self._on_mouse_move()
        return task.cont
        
    def _cancel_drag(self):
        """Cancel current drag operation."""
        if self.drag_controller.is_dragging():
            self.drag_controller.cancel_drag()
            self._rebuild_avatar()
            self._update_hint()
            
    def _on_undo(self):
        """Undo last action."""
        if self.history.undo():
            self._rebuild_avatar()
            self._update_sliders()
            self._update_hint()
            
    def _on_redo(self):
        """Redo last undone action."""
        if self.history.redo():
            self._rebuild_avatar()
            self._update_sliders()
            self._update_hint()
            
    def cleanup(self):
        """Clean up resources."""
        self.hide()
        
        if self.avatar:
            self.avatar.cleanup()
        if self.skeleton_renderer:
            self.skeleton_renderer.cleanup()
        if self.bone_picker:
            self.bone_picker.cleanup()
        if self.main_frame:
            self.main_frame.destroy()
