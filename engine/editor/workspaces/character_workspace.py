
from typing import Optional
from panda3d.core import NodePath, Point2, Vec3
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel

from engine.editor.workspace import Workspace
from engine.editor.selection import EditorSelection
from engine.editor.panels.bone_tree_panel import BoneTreePanel
from engine.editor.panels.transform_inspector import TransformInspectorPanel

# Reuse Logic/Rendering components from tools/common
from engine.editor.tools.common.orbit_camera import OrbitCamera
from engine.editor.tools.common.skeleton_renderer import SkeletonRenderer
from engine.editor.tools.common.editor_history import EditorHistory, EditorCommand
from engine.editor.tools.common.bone_picker import BonePicker
from engine.editor.tools.common.drag_controller import DragController, DragMode
from engine.editor.tools.common.transform_gizmo import TransformGizmo
from engine.editor.tools.common.symmetry_controller import SymmetryController
from engine.editor.tools.common.spline_controller import SplineController
from engine.editor.tools.common.spline_gizmo import SplineGizmo

from engine.animation.voxel_avatar import VoxelAvatar
from engine.animation.skeleton import HumanoidSkeleton
from engine.core.logger import get_logger

logger = get_logger(__name__)

# Copied from ModelEditor
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

class CharacterWorkspace(Workspace):
    """Character editing workspace."""
    
    def __init__(self, app):
        super().__init__(app, "Character")
        
        # Logic State
        self.history = EditorHistory(max_history=50)
        self.orbit_camera = OrbitCamera(app, focus_pos=(0, 0, 1))
        
        # 3D Objects
        self.avatar: Optional[VoxelAvatar] = None
        self.skeleton_renderer: Optional[SkeletonRenderer] = None
        
        # Tools
        self.bone_picker = None
        self.drag_controller = None
        self.transform_gizmo = None
        self.symmetry_controller = None
        self.current_mode = DragMode.MOVE
        self.symmetry_enabled = True
        
        # Spline
        self.spline_controller = None
        self.spline_gizmo = None
        self.spine_mode_enabled = False
        
        # Panels
        self.bone_panel: Optional[BoneTreePanel] = None
        self.inspector_panel: Optional[TransformInspectorPanel] = None
        self.hint_label = None
        
        self.update_task = None
        
        self._setup_scene()
        self._build_ui()
        
    def _setup_scene(self):
        """Initialize 3D content and tools."""
        # Create Avatar
        skeleton = HumanoidSkeleton()
        self.avatar = VoxelAvatar(
            self.app.render,
            skeleton=skeleton,
            body_color=(0.2, 0.8, 0.2, 1.0),
            validate=True
        )
        self.avatar.root.hide() # Hidden until entered
        
        # Renderer
        self.skeleton_renderer = SkeletonRenderer(self.app.render)
        self.skeleton_renderer.update_from_avatar(self.avatar)
        
        # Picker
        self.bone_picker = BonePicker(self.app, self.app.render)
        self.bone_picker.setup_skeleton(self.avatar.skeleton, self.avatar.bone_nodes)
        self.bone_picker.on_bone_selected = self._on_bone_clicked
        self.bone_picker.on_bone_hovered = self._on_bone_hovered
        
        # Drag
        self.drag_controller = DragController(
            self.app, 
            self.avatar.skeleton, 
            self.avatar.bone_nodes
        )
        self.drag_controller.on_transform_changed = self._on_transform_changed
        
        # Gizmo
        self.transform_gizmo = TransformGizmo(self.app.render)
        self.transform_gizmo.set_mode(TransformGizmo.MODE_TRANSLATE)
        
        # Symmetry
        self.symmetry_controller = SymmetryController(self.avatar.skeleton)
        self.symmetry_controller.set_enabled(self.symmetry_enabled)
        
        # Spline
        self.spline_controller = SplineController(self.avatar.skeleton)
        self.spline_gizmo = SplineGizmo(self.app.render, self.spline_controller)
        self.spline_gizmo.on_changed = self._on_spline_changed
        
    def _build_ui(self):
        """Build workspace UI panels."""
        # Left Panel: Bone Tree
        self.bone_panel = BoneTreePanel(self.app.aspect2d, self.selection, BONE_DISPLAY_NAMES)
        self.bone_panel.build_tree(self.avatar.skeleton if self.avatar else None)
        self.bone_panel.frame.hide()
        
        # Right Panel: Inspector
        # Callbacks map for sliders
        callbacks = {
            'pos': self._on_position_slider,
            'rot': self._on_rotation_slider,
            'length': self._on_length_slider
        }
        self.inspector_panel = TransformInspectorPanel(self.app.aspect2d, self.selection, callbacks)
        self.inspector_panel.frame.hide()
        
        # Hint Label (Bottom Center)
        from direct.gui.DirectGui import TextNode
        self.hint_label = DirectLabel(
            parent=self.app.aspect2d,
            text="",
            scale=0.03,
            pos=(0, 0, -0.9),
            text_fg=(0.8, 0.8, 0.8, 1),
            text_align=TextNode.ACenter,
            frameColor=(0.1, 0.1, 0.1, 0.5)
        )
        self.hint_label.hide()

    # ─────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────

    def enter(self):
        super().enter()
        self.avatar.root.show()
        self.skeleton_renderer.set_visible(True)
        self.orbit_camera.enable()
        self.bone_panel.frame.show()
        self.inspector_panel.frame.show()
        self.hint_label.show()
        
        # Setup selection observer
        if self.selection:
            self.selection.add_observer(self._on_selection_changed)
            
        self.update_task = self.app.taskMgr.add(self.update, "CharWorkspaceUpdate")
        
        # Force UI update
        self.bone_panel.build_tree(self.avatar.skeleton)
        
    def exit(self):
        super().exit()
        self.avatar.root.hide()
        self.skeleton_renderer.set_visible(False)
        self.orbit_camera.disable()
        self.bone_panel.frame.hide()
        self.inspector_panel.frame.hide()
        self.hint_label.hide()
        
        if self.selection:
            self.selection.remove_observer(self._on_selection_changed)
            
        if self.update_task:
            self.app.taskMgr.remove(self.update_task)
            self.update_task = None
            
    def update(self, task):
        self.orbit_camera.update()
        self._on_mouse_move()
        return task.cont
        
    def accept_shortcuts(self):
        self.app.accept('g', self._set_mode, [DragMode.TRANSLATE])
        self.app.accept('r', self._set_mode, [DragMode.ROTATE])
        self.app.accept('s', self._set_mode, [DragMode.SCALE])
        self.app.accept('f', self._frame_selection)
        self.app.accept("control-z", self._on_undo)
        self.app.accept("control-shift-z", self._on_redo)
        self.app.accept("mouse1", self._on_mouse_press)
        self.app.accept("mouse1-up", self._on_mouse_release)
        self.app.accept("wheel_up", self._on_scroll, [1])
        self.app.accept("wheel_down", self._on_scroll, [-1])
        
    # ─────────────────────────────────────────────────────────────────
    # Interaction Logic (Ported)
    # ─────────────────────────────────────────────────────────────────
    
    def _on_selection_changed(self, prop, value):
        if prop == "bone":
            self.skeleton_renderer.highlight_bone(value)
            self.bone_panel.update_selection(value)
            self.inspector_panel.update()
            
            # Attach gizmo
            if self.transform_gizmo and value in self.avatar.bone_nodes:
                self.transform_gizmo.attach_to(self.avatar.bone_nodes[value])

    def _on_bone_clicked(self, bone_name):
        if self.selection:
            self.selection.bone = bone_name # Triggers observer

    def _on_bone_hovered(self, bone_name):
        if bone_name and not self.drag_controller.is_dragging():
            self.hint_label['text'] = f"Click to select: {BONE_DISPLAY_NAMES.get(bone_name, bone_name)}"
        elif not self.drag_controller.is_dragging():
            self.hint_label['text'] = ""

    def _on_mouse_press(self):
        if not self.active or not self.app.mouseWatcherNode.hasMouse():
            return
        mpos = self.app.mouseWatcherNode.getMouse()
        bone = self.bone_picker.pick(Point2(mpos.x, mpos.y))
        if bone:
            if self.selection: self.selection.bone = bone
            self.drag_controller.begin_drag(bone, self.current_mode, Point2(mpos.x, mpos.y))
            
    def _on_mouse_release(self):
        if self.drag_controller.is_dragging():
            self.drag_controller.end_drag(self.history)
            self._rebuild_avatar()

    def _on_mouse_move(self):
        if not self.active or not self.app.mouseWatcherNode.hasMouse():
            return
        mpos = self.app.mouseWatcherNode.getMouse()
        if self.drag_controller.is_dragging():
            self.drag_controller.update_drag(Point2(mpos.x, mpos.y))
        else:
            self.bone_picker.update_hover(Point2(mpos.x, mpos.y))

    def _on_scroll(self, direction):
        # Todo: Implement scroll scale logic from ModelEditor
        pass
        
    def _set_mode(self, mode):
        self.current_mode = mode
        if self.transform_gizmo:
            if mode == DragMode.TRANSLATE: self.transform_gizmo.set_mode(TransformGizmo.MODE_TRANSLATE)
            elif mode == DragMode.ROTATE: self.transform_gizmo.set_mode(TransformGizmo.MODE_ROTATE)
            elif mode == DragMode.SCALE: self.transform_gizmo.set_mode(TransformGizmo.MODE_SCALE)
            
    def _frame_selection(self):
        if self.selection and self.selection.bone:
            bone = self.avatar.skeleton.get_bone(self.selection.bone)
            if bone:
                target = bone.node.getPos(self.app.render)
                self.orbit_camera.set_target(target)

    def _on_undo(self): self.history.undo(); self._rebuild_avatar()
    def _on_redo(self): self.history.redo(); self._rebuild_avatar()
    
    def _rebuild_avatar(self):
        skeleton = self.avatar.skeleton
        self.avatar.cleanup()
        self.avatar = VoxelAvatar(self.app.render, skeleton=skeleton, body_color=(0.2, 0.8, 0.2, 1.0))
        self.skeleton_renderer.update_from_avatar(self.avatar)
        self.bone_picker.setup_skeleton(self.avatar.skeleton, self.avatar.bone_nodes)
        self.drag_controller.set_skeleton(self.avatar.skeleton, self.avatar.bone_nodes)
        
        if self.selection and self.selection.bone:
            self.skeleton_renderer.highlight_bone(self.selection.bone)
            if self.selection.bone in self.avatar.bone_nodes:
                self.transform_gizmo.attach_to(self.avatar.bone_nodes[self.selection.bone])

    # Slider Callbacks (Simplified)
    def _on_position_slider(self, val): pass
    def _on_rotation_slider(self, val): pass
    def _on_length_slider(self, val): pass
    
    def _on_spline_changed(self):
        pass # Todo implementation

    def cleanup(self):
        super().cleanup()
        if self.avatar: self.avatar.cleanup()
        if self.bone_panel: self.bone_panel.cleanup()
        if self.inspector_panel: self.inspector_panel.cleanup()
