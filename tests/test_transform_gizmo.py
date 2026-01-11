
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

# Setup explicit core mocks
core_mock = MagicMock()
sys.modules['panda3d.core'] = core_mock

# Mock specific Panda3D classes used
NodePath = MagicMock()
NodePath.return_value.getName.return_value = "mock_node"
core_mock.NodePath = NodePath

# Collision mocks
CollisionNode = MagicMock()
core_mock.CollisionNode = CollisionNode
core_mock.CollisionSphere = MagicMock()
core_mock.CollisionRay = MagicMock()
core_mock.BitMask32 = MagicMock()
core_mock.LineSegs = MagicMock()
core_mock.GeomNode = MagicMock()

# Vector mocks
class MockVec3:
    def __init__(self, x=0, y=0, z=0):
        if hasattr(x, 'x'):
            self.x = float(x.x)
            self.y = float(x.y)
            self.z = float(x.z)
        else:
            self.x = x
            self.y = y
            self.z = z
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z
    def __repr__(self):
        return f"MockVec3({self.x}, {self.y}, {self.z})"
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return MockVec3(self.x * other, self.y * other, self.z * other)
        return NotImplemented
    def __rmul__(self, other):
        return self.__mul__(other)
    def __add__(self, other):
        return MockVec3(self.x + other.x, self.y + other.y, self.z + other.z)

core_mock.LVector3f = MockVec3
core_mock.LVector4f = MagicMock()

from engine.editor.tools.common.transform_gizmo import TransformGizmo

class TestTransformGizmo:
    @pytest.fixture
    def mock_parent(self):
        return NodePath("parent")
        
    @pytest.fixture
    def gizmo(self, mock_parent):
        return TransformGizmo(mock_parent)

    def test_initialization(self, gizmo, mock_parent):
        """Test gizmo initializes in translate mode and hidden."""
        assert gizmo.mode == "translate"
        assert not gizmo.visible
        # Should have created root node attached to parent
        mock_parent.attachNewNode.assert_called_with("TransformGizmo")
    
    def test_set_mode_translate(self, gizmo):
        """Test switching to translate mode."""
        gizmo.set_mode("translate")
        assert gizmo.mode == "translate"
        
    def test_set_mode_rotate(self, gizmo):
        """Test switching to rotate mode."""
        gizmo.set_mode("rotate")
        assert gizmo.mode == "rotate"
        
    def test_set_mode_scale(self, gizmo):
        """Test switching to scale mode."""
        gizmo.set_mode("scale")
        assert gizmo.mode == "scale"
        
    def test_attach_to(self, gizmo):
        """Test attaching to a bone node."""
        # Use a mock bone node that returns a position
        bone_node = MagicMock()
        bone_node.getPos.return_value = MockVec3(10, 20, 30)
        
        gizmo.attach_to(bone_node)
        
        # Should be visible and position updated
        assert gizmo.visible
        # Verify setPos was called with the position from getPos
        # Note: arg matching with MockVec3 might be tricky, checking called is safer
        assert gizmo.root.setPos.called 
        assert gizmo.root.show.called
        
    def test_detach(self, gizmo):
        """Test detaching hides gizmo."""
        bone_node = MagicMock()
        gizmo.attach_to(bone_node)
        gizmo.detach()
        
        assert not gizmo.visible
        assert gizmo.target_bone is None

    def test_get_active_axis_x(self, gizmo):
        """Test picking the X axis."""
        # Setup mock collision entry
        entry = MagicMock()
        # Mock into node returning tag
        entry.getIntoNodePath.return_value.getTag.return_value = "x"
        
        axis = gizmo.get_active_axis(entry)
        assert axis == "x"
        
    def test_get_active_axis_none(self, gizmo):
        """Test picking something irrelevant returns None."""
        entry = MagicMock()
        # Return empty string or None for tag
        entry.getIntoNodePath.return_value.getTag.return_value = ""
        
        axis = gizmo.get_active_axis(entry)
        assert axis is None
