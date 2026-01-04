"""
DragController: Converts mouse drag to bone transforms.

Handles move, rotate, and scale operations via mouse interaction.
"""

from enum import Enum
from typing import Optional, Tuple
from dataclasses import dataclass
from panda3d.core import NodePath, LVector3f, Point2, Point3
from engine.animation.skeleton import Skeleton, Bone
from engine.editor.tools.common.editor_history import EditorHistory, EditorCommand
from engine.core.logger import get_logger

logger = get_logger(__name__)


class DragMode(Enum):
    """Drag operation modes."""
    NONE = "none"
    MOVE = "move"
    ROTATE = "rotate"
    SCALE = "scale"


@dataclass
class DragState:
    """State during an active drag operation."""
    bone_name: str
    mode: DragMode
    start_mouse: Point2
    start_position: LVector3f
    start_rotation: LVector3f
    start_length: float
    

class DragController:
    """Converts mouse drag movements to bone transformations.
    
    Features:
    - Screen-space dragging for position
    - Circular dragging for rotation
    - Vertical dragging for scale
    - Throttled updates for performance
    """
    
    # Sensitivity multipliers
    MOVE_SENSITIVITY = 2.0
    ROTATE_SENSITIVITY = 180.0  # Degrees per screen width
    SCALE_SENSITIVITY = 2.0
    
    def __init__(self, app, skeleton: Skeleton, bone_nodes: dict):
        """Initialize drag controller.
        
        Args:
            app: EditorApp instance
            skeleton: Skeleton being edited
            bone_nodes: Dict mapping bone names to NodePaths
        """
        self.app = app
        self.skeleton = skeleton
        self.bone_nodes = bone_nodes
        
        # Current drag state
        self.drag_state: Optional[DragState] = None
        self.active = False
        
        # Transform change callback
        self.on_transform_changed: Optional[callable] = None
        
    def set_skeleton(self, skeleton: Skeleton, bone_nodes: dict):
        """Update skeleton reference.
        
        Args:
            skeleton: New skeleton
            bone_nodes: New bone nodes dict
        """
        self.skeleton = skeleton
        self.bone_nodes = bone_nodes
        
    def begin_drag(self, bone_name: str, mode: DragMode, mouse_pos: Point2) -> bool:
        """Start a drag operation.
        
        Args:
            bone_name: Name of bone to transform
            mode: Type of transformation
            mouse_pos: Starting mouse position
            
        Returns:
            True if drag started successfully
        """
        if not self.skeleton:
            return False
            
        bone = self.skeleton.get_bone(bone_name)
        if not bone:
            logger.warning(f"Cannot drag unknown bone: {bone_name}")
            return False
            
        # Store initial state for undo - use explicit float copies
        self.drag_state = DragState(
            bone_name=bone_name,
            mode=mode,
            start_mouse=Point2(float(mouse_pos.x), float(mouse_pos.y)),
            start_position=LVector3f(bone.local_transform.position),
            start_rotation=LVector3f(bone.local_transform.rotation),
            start_length=float(bone.length)
        )
        
        self.active = True
        logger.debug(f"Begin {mode.value} drag on {bone_name}")
        return True
        
    def update_drag(self, mouse_pos: Point2) -> bool:
        """Update transformation during drag.
        
        Args:
            mouse_pos: Current mouse position
            
        Returns:
            True if transform was updated
        """
        if not self.active or not self.drag_state:
            return False
            
        bone = self.skeleton.get_bone(self.drag_state.bone_name)
        if not bone:
            return False
            
        # Calculate mouse delta
        delta = Point2(
            mouse_pos.x - self.drag_state.start_mouse.x,
            mouse_pos.y - self.drag_state.start_mouse.y
        )
        
        # Apply transform based on mode
        if self.drag_state.mode == DragMode.MOVE:
            self._apply_move(bone, delta)
        elif self.drag_state.mode == DragMode.ROTATE:
            self._apply_rotate(bone, delta)
        elif self.drag_state.mode == DragMode.SCALE:
            self._apply_scale(bone, delta)
            
        # Notify listeners
        if self.on_transform_changed:
            self.on_transform_changed()
            
        return True
        
    def _apply_move(self, bone: Bone, delta: Point2):
        """Apply position change from mouse delta.
        
        Maps screen X→world X, screen Y→world Z (vertical).
        """
        # Get camera-relative directions
        # For simplicity, map screen X to world X, screen Y to world Z
        move_x = delta.x * self.MOVE_SENSITIVITY
        move_z = delta.y * self.MOVE_SENSITIVITY
        
        new_pos = LVector3f(
            self.drag_state.start_position.x + move_x,
            self.drag_state.start_position.y,  # Keep Y unchanged for now
            self.drag_state.start_position.z + move_z
        )
        
        bone.local_transform.position = new_pos
        
    def _apply_rotate(self, bone: Bone, delta: Point2):
        """Apply rotation change from mouse delta.
        
        Horizontal drag = heading (turn), vertical drag = pitch (tilt).
        """
        # Calculate rotation angles
        heading = delta.x * self.ROTATE_SENSITIVITY
        pitch = -delta.y * self.ROTATE_SENSITIVITY  # Invert for natural feel
        
        # Apply with constraints
        new_h = self.drag_state.start_rotation.x + heading
        new_p = self.drag_state.start_rotation.y + pitch
        new_r = self.drag_state.start_rotation.z  # Roll unchanged during drag
        
        # Clamp to bone constraints
        if bone.constraints:
            new_h, new_p, new_r = bone.constraints.clamp(new_h, new_p, new_r)
            
        bone.local_transform.rotation = LVector3f(new_h, new_p, new_r)
        
    def _apply_scale(self, bone: Bone, delta: Point2):
        """Apply scale change from mouse delta.
        
        Vertical drag changes bone length.
        """
        # Vertical movement changes length
        length_delta = delta.y * self.SCALE_SENSITIVITY
        new_length = max(0.05, self.drag_state.start_length + length_delta)
        
        bone.length = new_length
        
    def end_drag(self, history: EditorHistory) -> Optional[EditorCommand]:
        """End drag operation and create undo command.
        
        Args:
            history: Editor history for undo registration
            
        Returns:
            EditorCommand for undo/redo, or None if no change
        """
        if not self.active or not self.drag_state:
            return None
            
        bone = self.skeleton.get_bone(self.drag_state.bone_name)
        if not bone:
            self.active = False
            self.drag_state = None
            return None
            
        # Capture final state
        final_position = LVector3f(bone.local_transform.position)
        final_rotation = LVector3f(bone.local_transform.rotation)
        final_length = bone.length
        
        # Capture initial state from drag_state
        start_state = self.drag_state
        bone_name = start_state.bone_name
        
        # Create undo/redo command
        def execute():
            b = self.skeleton.get_bone(bone_name)
            if b:
                b.local_transform.position = final_position
                b.local_transform.rotation = final_rotation
                b.length = final_length
                
        def undo():
            b = self.skeleton.get_bone(bone_name)
            if b:
                b.local_transform.position = start_state.start_position
                b.local_transform.rotation = start_state.start_rotation
                b.length = start_state.start_length
                
        mode_name = start_state.mode.value.title()
        cmd = EditorCommand(execute, undo, f"{mode_name} {bone_name}")
        
        # Register with history (don't execute, already applied)
        history.add_command(cmd)
        
        # Reset state
        self.active = False
        self.drag_state = None
        
        logger.debug(f"End drag: {mode_name} {bone_name}")
        return cmd
        
    def cancel_drag(self):
        """Cancel current drag and restore original state."""
        if not self.active or not self.drag_state:
            return
            
        bone = self.skeleton.get_bone(self.drag_state.bone_name)
        if bone:
            # Restore original transforms
            bone.local_transform.position = self.drag_state.start_position
            bone.local_transform.rotation = self.drag_state.start_rotation
            bone.length = self.drag_state.start_length
            
        self.active = False
        self.drag_state = None
        logger.debug("Drag cancelled")
        
    def is_dragging(self) -> bool:
        """Check if a drag is in progress."""
        return self.active
