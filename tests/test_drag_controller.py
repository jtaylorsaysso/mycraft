"""
Tests for BonePicker and DragController.
"""

import pytest
from unittest.mock import MagicMock
from panda3d.core import LVector3f, Point2

from engine.animation.skeleton import HumanoidSkeleton
from engine.editor.tools.common.drag_controller import DragController, DragMode, DragState
from engine.editor.tools.common.editor_history import EditorHistory


def vectors_equal(v1: LVector3f, v2: LVector3f, tolerance: float = 0.001) -> bool:
    """Compare two LVector3f with tolerance."""
    return (
        abs(v1.x - v2.x) < tolerance and
        abs(v1.y - v2.y) < tolerance and
        abs(v1.z - v2.z) < tolerance
    )


class TestDragController:
    """Tests for DragController component."""
    
    @pytest.fixture
    def skeleton(self):
        """Create a test skeleton."""
        return HumanoidSkeleton()
        
    @pytest.fixture
    def drag_controller(self, skeleton):
        """Create a DragController with mock app."""
        mock_app = MagicMock()
        bone_nodes = {}  # Simplified for testing
        return DragController(mock_app, skeleton, bone_nodes)
        
    def test_begin_drag_valid_bone(self, drag_controller):
        """Test starting a drag on a valid bone."""
        mouse_pos = Point2(0.0, 0.0)
        result = drag_controller.begin_drag("hips", DragMode.MOVE, mouse_pos)
        
        assert result is True
        assert drag_controller.is_dragging()
        assert drag_controller.drag_state.bone_name == "hips"
        assert drag_controller.drag_state.mode == DragMode.MOVE
        
    def test_begin_drag_invalid_bone(self, drag_controller):
        """Test starting a drag on an invalid bone."""
        mouse_pos = Point2(0.0, 0.0)
        result = drag_controller.begin_drag("nonexistent_bone", DragMode.MOVE, mouse_pos)
        
        assert result is False
        assert not drag_controller.is_dragging()
        
    def test_cancel_drag_restores_state(self, drag_controller, skeleton):
        """Test that canceling a drag restores original transforms."""
        bone = skeleton.get_bone("hips")
        original_x = bone.local_transform.position.x
        original_y = bone.local_transform.position.y
        original_z = bone.local_transform.position.z
        
        # Start drag
        mouse_pos = Point2(0.0, 0.0)
        drag_controller.begin_drag("hips", DragMode.MOVE, mouse_pos)
        
        # Modify during drag
        bone.local_transform.position = LVector3f(1.0, 2.0, 3.0)
        
        # Cancel
        drag_controller.cancel_drag()
        
        assert not drag_controller.is_dragging()
        # Check individual components
        assert abs(bone.local_transform.position.x - original_x) < 0.001
        assert abs(bone.local_transform.position.y - original_y) < 0.001
        assert abs(bone.local_transform.position.z - original_z) < 0.001
        
    def test_drag_modes(self, drag_controller):
        """Test all drag modes can be started."""
        mouse_pos = Point2(0.0, 0.0)
        
        for mode in [DragMode.MOVE, DragMode.ROTATE, DragMode.SCALE]:
            result = drag_controller.begin_drag("spine", mode, mouse_pos)
            assert result is True
            assert drag_controller.drag_state.mode == mode
            drag_controller.cancel_drag()
            

class TestDragControllerWithHistory:
    """Tests for DragController integration with EditorHistory."""
    
    @pytest.fixture
    def setup(self):
        """Create skeleton, history, and drag controller."""
        skeleton = HumanoidSkeleton()
        history = EditorHistory()
        mock_app = MagicMock()
        controller = DragController(mock_app, skeleton, {})
        return skeleton, history, controller
        
    def test_end_drag_creates_command(self, setup):
        """Test that ending a drag creates an undoable command."""
        skeleton, history, controller = setup
        
        # Start and complete a drag
        mouse_pos = Point2(0.0, 0.0)
        controller.begin_drag("hips", DragMode.MOVE, mouse_pos)
        
        # Modify bone
        bone = skeleton.get_bone("hips")
        bone.local_transform.position = LVector3f(1.0, 0.0, 1.0)
        
        # End drag
        cmd = controller.end_drag(history)
        
        assert cmd is not None
        assert history.can_undo()
        assert "Move hips" in cmd.description
        
    def test_undo_restores_original(self, setup):
        """Test that undo restores original position."""
        skeleton, history, controller = setup
        
        bone = skeleton.get_bone("chest")
        original_x = bone.local_transform.position.x
        original_y = bone.local_transform.position.y
        original_z = bone.local_transform.position.z
        
        # Perform a drag operation
        controller.begin_drag("chest", DragMode.MOVE, Point2(0.0, 0.0))
        bone.local_transform.position = LVector3f(5.0, 5.0, 5.0)
        controller.end_drag(history)
        
        # Undo
        history.undo()
        
        # Check components individually
        assert abs(bone.local_transform.position.x - original_x) < 0.001
        assert abs(bone.local_transform.position.y - original_y) < 0.001
        assert abs(bone.local_transform.position.z - original_z) < 0.001


class TestDragModes:
    """Tests for specific drag mode behavior."""
    
    @pytest.fixture
    def setup(self):
        skeleton = HumanoidSkeleton()
        mock_app = MagicMock()
        controller = DragController(mock_app, skeleton, {})
        return skeleton, controller
        
    def test_scale_mode_records_initial_length(self, setup):
        """Test that scale mode correctly records initial bone length."""
        skeleton, controller = setup
        
        bone = skeleton.get_bone("spine")
        original_length = bone.length
        
        # Start scale drag
        start_pos = Point2(0.0, 0.0)
        result = controller.begin_drag("spine", DragMode.SCALE, start_pos)
        
        # Verify mode started and initial length recorded
        assert result is True
        assert controller.is_dragging()
        assert controller.drag_state.mode == DragMode.SCALE
        assert abs(controller.drag_state.start_length - original_length) < 0.001
        
    def test_move_mode_updates_position(self, setup):
        """Test that move mode affects bone position."""
        skeleton, controller = setup
        
        bone = skeleton.get_bone("head")
        original_x = bone.local_transform.position.x
        original_z = bone.local_transform.position.z
        
        # Start move drag
        controller.begin_drag("head", DragMode.MOVE, Point2(0.0, 0.0))
        controller.update_drag(Point2(0.5, 0.5))
        
        # Position should have changed (move affects X and Z)
        pos_changed = (
            abs(bone.local_transform.position.x - original_x) > 0.1 or
            abs(bone.local_transform.position.z - original_z) > 0.1
        )
        assert pos_changed
