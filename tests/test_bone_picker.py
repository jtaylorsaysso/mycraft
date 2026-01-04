"""
Tests for BonePicker.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from panda3d.core import Point2, NodePath, BitMask32

from engine.editor.tools.common.bone_picker import BonePicker
from engine.animation.skeleton import HumanoidSkeleton


@pytest.fixture
def mock_app():
    """Create a mock EditorApp."""
    app = MagicMock()
    app.camera = MagicMock()
    app.camNode = MagicMock()
    
    # Mock camera.attachNewNode
    picker_np = MagicMock()
    app.camera.attachNewNode.return_value = picker_np
    
    return app


@pytest.fixture
def mock_parent_node():
    """Create a mock parent NodePath."""
    return MagicMock(spec=NodePath)


@pytest.fixture
def skeleton():
    """Create a test skeleton."""
    return HumanoidSkeleton()


@pytest.fixture
def bone_picker(mock_app, mock_parent_node):
    """Create a BonePicker instance."""
    with patch('engine.editor.tools.common.bone_picker.CollisionTraverser'):
        with patch('engine.editor.tools.common.bone_picker.CollisionHandlerQueue'):
            with patch('engine.editor.tools.common.bone_picker.CollisionNode'):
                with patch('engine.editor.tools.common.bone_picker.CollisionRay'):
                    picker = BonePicker(mock_app, mock_parent_node)
                    return picker


class TestBonePicker:
    """Tests for BonePicker."""
    
    def test_initialization(self, bone_picker):
        """Test picker initializes with correct state."""
        assert bone_picker.enabled is True
        assert bone_picker.hovered_bone is None
        assert bone_picker.skeleton is None
        assert bone_picker.bone_colliders == {}
        
    def test_pick_mask_is_set(self, bone_picker):
        """Test that collision mask is properly configured."""
        assert BonePicker.PICK_MASK == BitMask32.bit(1)
        
    def test_setup_skeleton(self, bone_picker, skeleton):
        """Test setting up skeleton for picking."""
        bone_nodes = {
            "hips": MagicMock(spec=NodePath),
            "spine": MagicMock(spec=NodePath)
        }
        
        with patch.object(bone_picker, '_rebuild_colliders') as mock_rebuild:
            bone_picker.setup_skeleton(skeleton, bone_nodes)
            
            assert bone_picker.skeleton == skeleton
            assert bone_picker.bone_nodes == bone_nodes
            mock_rebuild.assert_called_once()
            
    def test_rebuild_colliders_creates_spheres(self, bone_picker, skeleton):
        """Test that rebuild creates collision spheres for bones."""
        # Create mock bone nodes
        bone_nodes = {}
        for bone_name in ["hips", "spine", "chest"]:
            mock_node = MagicMock(spec=NodePath)
            mock_collider_np = MagicMock(spec=NodePath)
            mock_collider_np.setTag = MagicMock()  # Explicitly add setTag
            mock_node.attachNewNode.return_value = mock_collider_np
            bone_nodes[bone_name] = mock_node
            
        bone_picker.skeleton = skeleton
        bone_picker.bone_nodes = bone_nodes
        
        with patch('engine.editor.tools.common.bone_picker.CollisionNode'):
            with patch('engine.editor.tools.common.bone_picker.CollisionSphere'):
                bone_picker._rebuild_colliders()
                
                # Should create colliders for all bones
                assert len(bone_picker.bone_colliders) == 3
                
    def test_rebuild_colliders_clears_existing(self, bone_picker):
        """Test that rebuild clears existing colliders."""
        # Add some existing colliders
        mock_np1 = MagicMock(spec=NodePath)
        mock_np2 = MagicMock(spec=NodePath)
        bone_picker.bone_colliders = {
            "old1": mock_np1,
            "old2": mock_np2
        }
        
        bone_picker.skeleton = None
        bone_picker.bone_nodes = None
        
        bone_picker._rebuild_colliders()
        
        # Should have called removeNode on old colliders
        mock_np1.removeNode.assert_called_once()
        mock_np2.removeNode.assert_called_once()
        assert bone_picker.bone_colliders == {}
        
    def test_get_bone_radius(self, bone_picker, skeleton):
        """Test bone radius calculation."""
        bone = skeleton.get_bone("hips")
        radius = bone_picker._get_bone_radius("hips", bone)
        
        assert radius == 0.25  # Hips should have specific radius
        
    def test_get_bone_radius_default(self, bone_picker, skeleton):
        """Test bone radius falls back to default."""
        bone = skeleton.get_bone("hips")
        radius = bone_picker._get_bone_radius("unknown_bone", bone)
        
        assert radius == 0.1  # Default radius
        
    def test_pick_when_disabled(self, bone_picker):
        """Test that pick returns None when disabled."""
        bone_picker.enabled = False
        
        result = bone_picker.pick(Point2(0, 0))
        
        assert result is None
        
    def test_pick_when_no_skeleton(self, bone_picker):
        """Test that pick returns None when no skeleton is set."""
        bone_picker.skeleton = None
        
        result = bone_picker.pick(Point2(0, 0))
        
        assert result is None
        
    def test_pick_with_no_collisions(self, bone_picker, skeleton):
        """Test pick returns None when no bones are hit."""
        bone_picker.skeleton = skeleton
        bone_picker.handler.getNumEntries.return_value = 0
        
        result = bone_picker.pick(Point2(0, 0))
        
        assert result is None
        
    def test_pick_returns_closest_bone(self, bone_picker, skeleton):
        """Test that pick returns the closest bone when multiple are hit."""
        bone_picker.skeleton = skeleton
        bone_picker.handler.getNumEntries.return_value = 2
        
        # Mock collision entry
        mock_entry = MagicMock()
        mock_into_node = MagicMock()
        mock_into_node.getTag.return_value = "hips"
        mock_entry.getIntoNodePath.return_value = mock_into_node
        
        bone_picker.handler.getEntry.return_value = mock_entry
        
        result = bone_picker.pick(Point2(0, 0))
        
        assert result == "hips"
        bone_picker.handler.sortEntries.assert_called_once()
        
    def test_update_hover_calls_callback(self, bone_picker, skeleton):
        """Test that update_hover calls callback when hover changes."""
        bone_picker.skeleton = skeleton
        callback = MagicMock()
        bone_picker.on_bone_hovered = callback
        
        # Mock pick to return a bone
        with patch.object(bone_picker, 'pick', return_value="spine"):
            bone_picker.update_hover(Point2(0, 0))
            
            callback.assert_called_once_with("spine")
            assert bone_picker.hovered_bone == "spine"
            
    def test_update_hover_no_callback_when_same(self, bone_picker, skeleton):
        """Test that hover callback isn't called when bone doesn't change."""
        bone_picker.skeleton = skeleton
        bone_picker.hovered_bone = "spine"
        callback = MagicMock()
        bone_picker.on_bone_hovered = callback
        
        # Mock pick to return same bone
        with patch.object(bone_picker, 'pick', return_value="spine"):
            bone_picker.update_hover(Point2(0, 0))
            
            callback.assert_not_called()
            
    def test_handle_click_calls_callback(self, bone_picker, skeleton):
        """Test that handle_click calls selection callback."""
        bone_picker.skeleton = skeleton
        callback = MagicMock()
        bone_picker.on_bone_selected = callback
        
        # Mock pick to return a bone
        with patch.object(bone_picker, 'pick', return_value="chest"):
            result = bone_picker.handle_click(Point2(0, 0))
            
            assert result == "chest"
            callback.assert_called_once_with("chest")
            
    def test_handle_click_when_disabled(self, bone_picker):
        """Test that handle_click returns None when disabled."""
        bone_picker.enabled = False
        callback = MagicMock()
        bone_picker.on_bone_selected = callback
        
        result = bone_picker.handle_click(Point2(0, 0))
        
        assert result is None
        callback.assert_not_called()
        
    def test_set_enabled(self, bone_picker):
        """Test enabling and disabling picker."""
        bone_picker.set_enabled(False)
        assert not bone_picker.enabled
        
        bone_picker.set_enabled(True)
        assert bone_picker.enabled
        
    def test_cleanup_removes_colliders(self, bone_picker):
        """Test that cleanup removes all collision nodes."""
        # Add some colliders
        mock_np1 = MagicMock(spec=NodePath)
        mock_np2 = MagicMock(spec=NodePath)
        bone_picker.bone_colliders = {
            "bone1": mock_np1,
            "bone2": mock_np2
        }
        
        bone_picker.cleanup()
        
        mock_np1.removeNode.assert_called_once()
        mock_np2.removeNode.assert_called_once()
        assert bone_picker.bone_colliders == {}
        
    def test_cleanup_removes_picker_ray(self, bone_picker):
        """Test that cleanup removes picker ray node."""
        bone_picker.cleanup()
        
        bone_picker.picker_np.removeNode.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
