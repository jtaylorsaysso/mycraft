"""
Tests for OrbitCamera.
"""

import pytest
from unittest.mock import MagicMock, Mock

from engine.editor.tools.common.orbit_camera import OrbitCamera


@pytest.fixture
def mock_app():
    """Create a mock Panda3D app."""
    app = MagicMock()
    app.camera = MagicMock()
    app.render = MagicMock()
    app.win = MagicMock()
    
    # Mock node hierarchy
    pivot_node = MagicMock()
    app.render.attachNewNode.return_value = pivot_node
    
    return app


@pytest.fixture
def orbit_camera(mock_app):
    """Create an OrbitCamera instance."""
    return OrbitCamera(mock_app, focus_pos=(0, 0, 1))


class TestOrbitCamera:
    """Tests for OrbitCamera."""
    
    def test_initialization(self, orbit_camera):
        """Test camera initializes with default values."""
        assert orbit_camera.distance == 5.0
        assert orbit_camera.heading == 0.0
        assert orbit_camera.pitch == -20.0
        assert orbit_camera.focus == (0, 0, 1)
        assert not orbit_camera.is_orbiting
        
    def test_initialization_custom_focus(self, mock_app):
        """Test camera initializes with custom focus point."""
        camera = OrbitCamera(mock_app, focus_pos=(5, 10, 2))
        assert camera.focus == (5, 10, 2)
        
    def test_enable_creates_pivot(self, orbit_camera, mock_app):
        """Test that enable() creates pivot node."""
        orbit_camera.enable()
        
        mock_app.render.attachNewNode.assert_called_once_with("EditorCamPivot")
        assert orbit_camera.pivot is not None
        
    def test_enable_saves_camera_state(self, orbit_camera, mock_app):
        """Test that enable() saves original camera state."""
        orbit_camera.enable()
        
        assert orbit_camera.saved_cam_parent is not None
        assert orbit_camera.saved_cam_transform is not None
        
    def test_enable_binds_inputs(self, orbit_camera, mock_app):
        """Test that enable() binds mouse inputs."""
        orbit_camera.enable()
        
        # Check that accept was called for all inputs
        calls = [call[0][0] for call in mock_app.accept.call_args_list]
        assert "mouse3" in calls
        assert "mouse3-up" in calls
        assert "wheel_up" in calls
        assert "wheel_down" in calls
        
    def test_disable_restores_camera(self, orbit_camera, mock_app):
        """Test that disable() restores camera state."""
        orbit_camera.enable()
        orbit_camera.disable()
        
        mock_app.camera.reparentTo.assert_called()
        mock_app.camera.setTransform.assert_called()
        
    def test_disable_removes_pivot(self, orbit_camera, mock_app):
        """Test that disable() removes pivot node."""
        orbit_camera.enable()
        pivot = orbit_camera.pivot
        
        orbit_camera.disable()
        
        pivot.removeNode.assert_called_once()
        assert orbit_camera.pivot is None
        
    def test_disable_unbinds_inputs(self, orbit_camera, mock_app):
        """Test that disable() unbinds mouse inputs."""
        orbit_camera.enable()
        orbit_camera.disable()
        
        # Check that ignore was called for all inputs
        calls = [call[0][0] for call in mock_app.ignore.call_args_list]
        assert "mouse3" in calls
        assert "mouse3-up" in calls
        assert "wheel_up" in calls
        assert "wheel_down" in calls
        
    def test_zoom_in_decreases_distance(self, orbit_camera):
        """Test that zoom in decreases distance."""
        orbit_camera.enable()
        initial_distance = orbit_camera.distance
        
        orbit_camera._zoom_in()
        
        assert orbit_camera.distance < initial_distance
        
    def test_zoom_in_respects_minimum(self, orbit_camera):
        """Test that zoom in doesn't go below minimum distance."""
        orbit_camera.enable()
        orbit_camera.distance = 1.0
        
        orbit_camera._zoom_in()
        
        assert orbit_camera.distance == 1.0  # Should not go below 1.0
        
    def test_zoom_out_increases_distance(self, orbit_camera):
        """Test that zoom out increases distance."""
        orbit_camera.enable()
        initial_distance = orbit_camera.distance
        
        orbit_camera._zoom_out()
        
        assert orbit_camera.distance > initial_distance
        
    def test_zoom_out_respects_maximum(self, orbit_camera):
        """Test that zoom out doesn't exceed maximum distance."""
        orbit_camera.enable()
        orbit_camera.distance = 30.0
        
        orbit_camera._zoom_out()
        
        assert orbit_camera.distance == 30.0  # Should not go above 30.0
        
    def test_start_orbit_sets_flag(self, orbit_camera, mock_app):
        """Test that starting orbit sets is_orbiting flag."""
        orbit_camera.enable()
        
        orbit_camera._start_orbit()
        
        assert orbit_camera.is_orbiting
        
    def test_stop_orbit_clears_flag(self, orbit_camera, mock_app):
        """Test that stopping orbit clears is_orbiting flag."""
        orbit_camera.enable()
        orbit_camera._start_orbit()
        
        orbit_camera._stop_orbit()
        
        assert not orbit_camera.is_orbiting
        
    def test_update_does_nothing_when_not_orbiting(self, orbit_camera, mock_app):
        """Test that update() does nothing when not orbiting."""
        orbit_camera.enable()
        initial_heading = orbit_camera.heading
        initial_pitch = orbit_camera.pitch
        
        orbit_camera.update()
        
        assert orbit_camera.heading == initial_heading
        assert orbit_camera.pitch == initial_pitch
        
    def test_pitch_clamping_upper_bound(self, orbit_camera, mock_app):
        """Test that pitch is clamped to upper bound."""
        orbit_camera.enable()
        orbit_camera.pitch = 89.0
        orbit_camera.is_orbiting = True
        
        # Mock mouse movement upward
        mock_pointer = MagicMock()
        mock_pointer.getX.return_value = 100
        mock_pointer.getY.return_value = 0  # Moving up
        mock_app.win.getPointer.return_value = mock_pointer
        
        orbit_camera.last_mouse_x = 100
        orbit_camera.last_mouse_y = 100  # Large delta
        
        orbit_camera.update()
        
        assert orbit_camera.pitch <= 89
        
    def test_pitch_clamping_lower_bound(self, orbit_camera, mock_app):
        """Test that pitch is clamped to lower bound."""
        orbit_camera.enable()
        orbit_camera.pitch = -89.0
        orbit_camera.is_orbiting = True
        
        # Mock mouse movement downward
        mock_pointer = MagicMock()
        mock_pointer.getX.return_value = 100
        mock_pointer.getY.return_value = 200  # Moving down
        mock_app.win.getPointer.return_value = mock_pointer
        
        orbit_camera.last_mouse_x = 100
        orbit_camera.last_mouse_y = 100  # Large delta
        
        orbit_camera.update()
        
        assert orbit_camera.pitch >= -89
        
    def test_set_focus_updates_position(self, orbit_camera):
        """Test that set_focus() updates focus point."""
        orbit_camera.enable()
        
        orbit_camera.set_focus(10, 20, 5)
        
        assert orbit_camera.focus == (10, 20, 5)
        orbit_camera.pivot.setPos.assert_called_with(10, 20, 5)
        
    def test_set_focus_before_enable(self, orbit_camera):
        """Test that set_focus() works before enable() is called."""
        orbit_camera.set_focus(5, 5, 5)
        
        assert orbit_camera.focus == (5, 5, 5)
        # Should not crash even though pivot is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
