"""
ModelEditor: Standalone editor for VoxelAvatar skeleton editing.

Part of the standalone editor suite - works without game runtime.

Features Spore-inspired mouse-controlled transformations:
- Click to select bones in 3D viewport
- Drag to move/rotate/scale
- Inline contextual hints for learning
"""

from typing import Optional
from panda3d.core import NodePath, Point2
from direct.gui.DirectGui import DirectFrame

from engine.editor.tools.common.orbit_camera import OrbitCamera
from engine.editor.tools.common.skeleton_renderer import SkeletonRenderer
from engine.editor.tools.common.editor_history import EditorHistory
from engine.editor.tools.common.bone_picker import BonePicker
from engine.editor.tools.common.drag_controller import DragController, DragMode
from engine.editor.tools.common.transform_gizmo import TransformGizmo
from engine.editor.tools.common.symmetry_controller import SymmetryController
from engine.editor.tools.common.spline_controller import SplineController
from engine.editor.tools.common.spline_gizmo import SplineGizmo
from engine.editor.tools.model_editor_ui import ModelEditorUI
from engine.editor.tools.slider_panel import SliderPanel
from engine.editor.selection import EditorSelection
from engine.animation.voxel_avatar import VoxelAvatar
from engine.animation.skeleton import HumanoidSkeleton
from engine.core.logger import get_logger

logger = get_logger(__name__)

# Bone display names for UI
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
        self.transform_gizmo: Optional[TransformGizmo] = None
        self.symmetry_controller: Optional[SymmetryController] = None
        self.current_mode = DragMode.MOVE
        self.symmetry_enabled = True
        
        # UI components
        self.ui: Optional[ModelEditorUI] = None
        self.slider_panel: Optional[SliderPanel] = None
        
        # Spine manipulation
        self.spline_controller: Optional[SplineController] = None
        self.spline_gizmo: Optional[SplineGizmo] = None
        self.spine_mode_enabled = False
        
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
            if self.slider_panel:
                self.slider_panel.update()
            if self.skeleton_renderer:
                self.skeleton_renderer.highlight_bone(value)
                
    def _setup(self):
        """Initialize editor UI and 3D content."""
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
        
        # Transform gizmo
        self.transform_gizmo = TransformGizmo(self.app.render)
        self.transform_gizmo.set_mode(TransformGizmo.MODE_TRANSLATE)
        
        # Symmetry controller
        self.symmetry_controller = SymmetryController(self.avatar.skeleton)
        self.symmetry_controller.set_enabled(self.symmetry_enabled)
        
        # Spine manipulation
        self.spline_controller = SplineController(self.avatar.skeleton)
        self.spline_gizmo = SplineGizmo(self.app.render, self.spline_controller)
        self.spline_gizmo.on_changed = self._on_spline_changed
        
        # Build UI
        self.ui = ModelEditorUI(self.app.aspect2d, self)
        self.slider_panel = SliderPanel(self.app.aspect2d, self)
        
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
        
        # Symmetry toggle
        self.symmetry_button = DirectButton(
            parent=toolbar,
            text="✓ Symmetry",
            scale=0.028,
            pos=(-0.25, 0, 0.90),
            frameColor=COLOR_BUTTON_ACTIVE if self.symmetry_enabled else COLOR_BUTTON,
            text_fg=(1, 1, 1, 1),
            command=self._toggle_symmetry
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
    
    # ─────────────────────────────────────────────────────────────────
    # Mode & Selection
    # ─────────────────────────────────────────────────────────────────
    
    def _set_mode(self, mode: DragMode):
        """Set current transform mode."""
        self.current_mode = mode
        
        if self.ui:
            self.ui.set_active_mode(mode)
            
        # Update gizmo mode
        if self.transform_gizmo:
            if mode == DragMode.MOVE:
                self.transform_gizmo.set_mode(TransformGizmo.MODE_TRANSLATE)
            elif mode == DragMode.ROTATE:
                self.transform_gizmo.set_mode(TransformGizmo.MODE_ROTATE)
            elif mode == DragMode.SCALE:
                self.transform_gizmo.set_mode(TransformGizmo.MODE_SCALE)
            
        self._update_hint()
        
    def _select_bone(self, bone_name: str):
        """Select bone from UI list."""
        if self.selection:
            self.selection.bone = bone_name
        if self.skeleton_renderer:
            self.skeleton_renderer.highlight_bone(bone_name)
            
        # Attach gizmo to selected bone
        if self.transform_gizmo and bone_name in self.avatar.bone_nodes:
            self.transform_gizmo.attach_to(self.avatar.bone_nodes[bone_name])
            
        self._update_hint()
        if self.slider_panel:
            self.slider_panel.update()
        
    def _toggle_symmetry(self):
        """Toggle symmetry mode on/off."""
        self.symmetry_enabled = not self.symmetry_enabled
        
        if self.symmetry_controller:
            self.symmetry_controller.set_enabled(self.symmetry_enabled)
            
        # Update UI
        if self.ui:
            self.ui.set_symmetry_active(self.symmetry_enabled)
            
        status = "enabled" if self.symmetry_enabled else "disabled"
        self._set_hint(f"Symmetry {status}")
    
    def _toggle_spine_mode(self):
        """Toggle spine manipulation mode on/off."""
        self.spine_mode_enabled = not self.spine_mode_enabled
        
        if self.spine_mode_enabled:
            # Initialize spline from current skeleton
            if self.spline_controller:
                self.spline_controller.initialize_from_skeleton()
                
            # Show spline gizmo
            if self.spline_gizmo:
                self.spline_gizmo.show()
                
            # Disable normal bone selection
            if self.bone_picker:
                self.bone_picker.set_enabled(False)
                
            # Hide transform gizmo
            if self.transform_gizmo:
                self.transform_gizmo.set_visible(False)
                
            self._set_hint("Spine Mode: Drag control points to bend spine")
        else:
            # Hide spline gizmo
            if self.spline_gizmo:
                self.spline_gizmo.hide()
                
            # Re-enable bone selection
            if self.bone_picker:
                self.bone_picker.set_enabled(True)
                
            # Show transform gizmo
            if self.transform_gizmo:
                self.transform_gizmo.set_visible(True)
                
            self._update_hint()
    
    def _on_spline_changed(self):
        """Handle spline control point changes."""
        # Update bones from spline
        if self.spline_controller:
            self.spline_controller.update_from_spline()
            
        # Rebuild avatar to reflect changes
        self._rebuild_avatar()
            
    # ─────────────────────────────────────────────────────────────────
    # Hints & Feedback
    # ─────────────────────────────────────────────────────────────────
    
    def _set_hint(self, text: str):
        """Set hint bar text."""
        if self.ui:
            self.ui.set_hint(text)
            
    def _update_hint(self):
        """Update hint based on current state."""
        if not self.selection or not self.selection.bone:
            self._set_hint("Click a bone to select it")
        else:
            bone_name = BONE_DISPLAY_NAMES.get(self.selection.bone, self.selection.bone)
            mode_name = self.current_mode.value.title()
            self._set_hint(f"Selected: {bone_name} | Drag to {mode_name} | Scroll to Scale")
            

        
    # ─────────────────────────────────────────────────────────────────
    # File I/O
    # ─────────────────────────────────────────────────────────────────
    
    def _on_save_request(self):
        """Show save dialog."""
        if self.ui:
            self.ui.show_io_dialog("Save Avatar As:", self._execute_save, lambda: None)
            
    def _execute_save(self, filename: str):
        """Save current avatar."""
        if not filename:
            return
        try:
            self.app.asset_manager.save_avatar(self.avatar, filename)
            self._set_hint(f"Saved to {filename}.mca")
        except Exception as e:
            logger.error(f"Failed to save: {e}")
            self._set_hint("Save Failed! Check logs.")

    def _on_load_request(self):
        """Show load dialog."""
        if self.ui:
            self.ui.show_io_dialog("Load Avatar:", self._execute_load, lambda: None)
            
    def _execute_load(self, filename: str):
        """Load avatar."""
        if not filename:
            return
        try:
            new_avatar = self.app.asset_manager.load_avatar(filename, self.app.render)
            
            # Clean up old
            if self.avatar:
                self.avatar.cleanup()
            
            self.avatar = new_avatar
            # We need to ensure we hide the root if editor was hidden? 
            # Assuming load happens while editor is visible.
            
            # Setup editor for new avatar
            self._setup_editor_for_avatar()
            
            self._set_hint(f"Loaded {filename}.mca")
        except Exception as e:
            logger.error(f"Failed to load: {e}")
            self._set_hint(f"Load Failed: {e}")
            
    def _setup_editor_for_avatar(self):
        """Refresh editor components for current avatar."""
        if self.skeleton_renderer:
            self.skeleton_renderer.update_from_avatar(self.avatar)
            
        if self.bone_picker:
            self.bone_picker.setup_skeleton(self.avatar.skeleton, self.avatar.bone_nodes)
            
        if self.drag_controller:
            self.drag_controller.set_skeleton(self.avatar.skeleton, self.avatar.bone_nodes)
            
        if self.symmetry_controller:
            self.symmetry_controller.skeleton = self.avatar.skeleton
            
        if self.spline_controller:
            self.spline_controller.set_skeleton(self.avatar.skeleton)
            
        if self.ui:
            # Rebuild bone panel or update it?
            # ModelEditorUI._build_bone_panel is static structure, but bone list is dynamic?
            # Looking at build_bone_panel, it iterates self.avatar.skeleton.bones.
            # We might need to refresh it.
            # Simplified: just warn user "UI might need restart" or implement refresh.
            pass

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
        
        if self.ui:
            self.ui.show()
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
        
        if self.ui:
            self.ui.hide()
        if self.slider_panel:
            self.slider_panel.hide()
            
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
