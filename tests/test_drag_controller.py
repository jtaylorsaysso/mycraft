
import pytest
import sys
from unittest.mock import MagicMock, Mock, patch

# Mock Panda3D modules
sys.modules['direct'] = MagicMock()
sys.modules['direct.showbase'] = MagicMock()
sys.modules['direct.showbase.DirectObject'] = MagicMock()
sys.modules['direct.showbase.ShowBase'] = MagicMock()
sys.modules['direct.gui'] = MagicMock()
sys.modules['direct.gui.DirectGui'] = MagicMock()
sys.modules['direct.interval'] = MagicMock()
sys.modules['direct.interval.IntervalGlobal'] = MagicMock()
sys.modules['direct.fsm'] = MagicMock()
sys.modules['direct.fsm.FSM'] = MagicMock()
sys.modules['panda3d'] = MagicMock()

core_mock = MagicMock()
sys.modules['panda3d.core'] = core_mock

# Vector mocking
class MockVec3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        if hasattr(x, 'x'):
            self.x = float(x.x) if hasattr(x, 'x') else 0.0
            self.y = float(x.y) if hasattr(x, 'y') else 0.0
            self.z = float(x.z) if hasattr(x, 'z') else 0.0
        else:
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)
        
    def __add__(self, other):
        if not isinstance(other, MockVec3): return self
        return MockVec3(self.x + other.x, self.y + other.y, self.z + other.z)
        
    def __sub__(self, other):
        if not isinstance(other, MockVec3): return self
        return MockVec3(self.x - other.x, self.y - other.y, self.z - other.z)
        
    def getX(self): return self.x
    def getY(self): return self.y
    def getZ(self): return self.z
    
    def __repr__(self): return f"Vec3({self.x}, {self.y}, {self.z})"

class MockPoint2:
    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)
    
    def __sub__(self, other):
        return MockPoint2(self.x - other.x, self.y - other.y)

    def getX(self): return self.x
    def getY(self): return self.y

core_mock.Point2 = MockPoint2
core_mock.Point3 = MockVec3
core_mock.LVector3f = MockVec3

from engine.editor.tools.common.drag_controller import DragController, DragMode, DragState
from engine.animation.skeleton import Skeleton, Bone
from engine.editor.tools.common.editor_history import EditorHistory

class TestDragController:
    @pytest.fixture
    def mock_app(self):
        app = MagicMock()
        # Mock camera for screen mapping
        app.camera = MagicMock()
        # Mock aspect2d/render
        app.render = MagicMock()
        return app
        
    @pytest.fixture
    def mock_bone(self):
        bone = MagicMock(spec=Bone)
        bone.name = "test_bone"
        
        # Setup local_transform structure
        # We need an object that holds position/rotation attributes
        transform = MagicMock()
        transform.position = MockVec3(0, 0, 0)
        transform.rotation = MockVec3(0, 0, 0)
        
        bone.local_transform = transform
        bone.length = 1.0
        return bone

    @pytest.fixture
    def mock_skeleton(self, mock_bone):
        skel = MagicMock(spec=Skeleton)
        skel.get_bone.return_value = mock_bone
        return skel
        
    @pytest.fixture
    def controller(self, mock_app, mock_skeleton):
        return DragController(mock_app, mock_skeleton, {})
        
    def test_initialization(self, controller):
        assert not controller.is_dragging()
        assert controller.drag_state is None
        
    def test_begin_drag(self, controller, mock_skeleton):
        """Test starting a drag operation."""
        start_pos = MagicMock() # Point2
        
        success = controller.begin_drag("test_bone", DragMode.MOVE, start_pos)
        
        assert success
        assert controller.is_dragging()
        assert controller.drag_state.mode == DragMode.MOVE
        assert controller.drag_state.bone_name == "test_bone"
        
        # Should have captured initial state
        mock_skeleton.get_bone.assert_called_with("test_bone")
        
    def test_update_drag_no_drag(self, controller):
        """Test update returns false if not dragging."""
        assert not controller.update_drag(MagicMock())
        
    def test_update_drag_move(self, controller, mock_bone):
        """Test updating a move drag."""
        start_pos = MockPoint2(0, 0)
        
        controller.begin_drag("test_bone", DragMode.MOVE, start_pos)
        
        # Move mouse
        curr_pos = MockPoint2(0.5, 0.5) # Delta = 0.5
        
        updated = controller.update_drag(curr_pos)
        
        assert updated
        # Correctly updated position on local_transform
        # Sensitivity is 2.0. Delta 0.5 -> 1.0 movement.
        assert mock_bone.local_transform.position.x == 1.0
        assert mock_bone.local_transform.position.z == 1.0

    def test_end_drag_creates_command(self, controller):
        """Test ending drag returns an undo command."""
        history = MagicMock(spec=EditorHistory)
        start_pos = MockPoint2(0, 0)
        
        controller.begin_drag("test_bone", DragMode.MOVE, start_pos)
        cmd = controller.end_drag(history)
        
        assert cmd is not None
        assert not controller.is_dragging()
        
    def test_cancel_drag(self, controller, mock_bone):
        """Test cancelling reverts changes."""
        start_pos = MockPoint2(0, 0)
        
        # Explicit initial state
        mock_bone.local_transform.position = MockVec3(10, 20, 30)
        
        controller.begin_drag("test_bone", DragMode.MOVE, start_pos)
        
        # Simulate change
        mock_bone.local_transform.position = MockVec3(99, 99, 99)
        
        controller.cancel_drag()
        
        assert not controller.is_dragging()
        # Verify it reverted to original values
        assert mock_bone.local_transform.position.x == 10
        assert mock_bone.local_transform.position.y == 20
        assert mock_bone.local_transform.position.z == 30
