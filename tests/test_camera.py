
import unittest
from unittest.mock import MagicMock
from panda3d.core import LVector3f

from engine.rendering.exploration_camera import ExplorationCamera
from engine.rendering.first_person_camera import FirstPersonCamera
from engine.rendering.base_camera import CameraUpdateContext
from engine.components.camera_state import CameraState, CameraMode

class TestCamera(unittest.TestCase):
    def test_exploration_camera_update(self):
        mock_node = MagicMock()
        mock_node.getPos.return_value = LVector3f(0, 0, 0)
        
        cam = ExplorationCamera(mock_node)
        
        # Create CameraState component
        camera_state = CameraState(
            mode=CameraMode.EXPLORATION,
            yaw=0.0,
            pitch=-15.0,
            distance=10.0,
            current_distance=10.0
        )
        
        # Initial State
        self.assertEqual(camera_state.yaw, 0.0)
        self.assertEqual(camera_state.pitch, -15.0)
        
        # Simulated Input: Move mouse right (positive DX)
        # Note: mouse_delta from InputManager is already normalized per-frame,
        # so we don't multiply by dt (it's framerate-independent already)
        dt = 0.016
        dx = 0.01  # Small normalized delta (like from InputManager)
        dy = 0.0
        
        # Create update context
        ctx = CameraUpdateContext(
            camera_node=mock_node,
            camera_state=camera_state,
            target_position=LVector3f(0, 0, 0),
            player_velocity=LVector3f(0, 0, 0),
            mouse_delta=(dx, dy),
            dt=dt
        )
        
        cam.update(ctx)
        
        # Check Yaw Update
        # yaw += dx * sensitivity (no dt multiplication)
        expected_yaw = 0.0 + (0.01 * 40.0)
        self.assertAlmostEqual(camera_state.yaw, expected_yaw, places=4)
        self.assertTrue(camera_state.yaw > 0)
        
        # Check Node Update
        mock_node.setPos.assert_called()
        mock_node.lookAt.assert_called()
        
    def test_first_person_camera_update(self):
        mock_node = MagicMock()
        cam = FirstPersonCamera(mock_node)
        
        # Create CameraState component
        camera_state = CameraState(
            mode=CameraMode.FIRST_PERSON,
            yaw=0.0,
            pitch=0.0
        )
        
        # Create update context
        ctx = CameraUpdateContext(
            camera_node=mock_node,
            camera_state=camera_state,
            target_position=LVector3f(0, 0, 0),
            player_velocity=LVector3f(0, 0, 0),
            mouse_delta=(10.0, 5.0),
            dt=0.016
        )
        
        cam.update(ctx)
        
        self.assertTrue(camera_state.yaw > 0)
        self.assertTrue(camera_state.pitch < 0) # Pitch is inverted (down is positive dy)
        mock_node.setHpr.assert_called()
        mock_node.setPos.assert_called()
    
    def test_exploration_camera_auto_center(self):
        """Test that auto-centering activates when moving without mouse input."""
        mock_node = MagicMock()
        mock_node.getPos.return_value = LVector3f(0, 0, 0)
        
        cam = ExplorationCamera(mock_node)
        
        # Create CameraState with auto-centering enabled
        camera_state = CameraState(
            mode=CameraMode.EXPLORATION,
            yaw=45.0,  # Camera is offset from player direction
            pitch=0.0,
            distance=5.0,
            current_distance=5.0,
            auto_center_strength=1.0,  # Full auto-center for testing
            mouse_moved_recently=0.0  # No recent mouse movement
        )
        
        # Player moving forward (north)
        player_velocity = LVector3f(0, 5, 0)
        
        # Create update context with no mouse movement
        ctx = CameraUpdateContext(
            camera_node=mock_node,
            camera_state=camera_state,
            target_position=LVector3f(0, 0, 0),
            player_velocity=player_velocity,
            mouse_delta=(0, 0),
            dt=0.1
        )
        
        initial_yaw = camera_state.yaw
        cam.update(ctx)
        
        # Camera should have rotated toward behind player (180°)
        # Since player is moving north (0°), camera should move toward 180°
        # With yaw at 45°, it should move closer to 180°
        self.assertNotEqual(camera_state.yaw, initial_yaw, 
                           "Auto-center should change yaw when moving")
    
    def test_exploration_camera_side_offset_framing(self):
        """Test that look-at target shifts opposite to side_offset for OTS framing."""
        mock_node = MagicMock()
        mock_node.getPos.return_value = LVector3f(0, 0, 0)
        
        # Create camera with positive side offset (camera to the right)
        cam = ExplorationCamera(mock_node, side_offset=2.0)
        
        camera_state = CameraState(
            mode=CameraMode.EXPLORATION,
            yaw=0.0,
            pitch=0.0,
            distance=5.0,
            current_distance=5.0
        )
        
        ctx = CameraUpdateContext(
            camera_node=mock_node,
            camera_state=camera_state,
            target_position=LVector3f(0, 0, 0),
            player_velocity=LVector3f(0, 0, 0),
            mouse_delta=(0, 0),
            dt=0.016
        )
        
        cam.update(ctx)
        
        # Capture the lookAt call argument
        look_at_call = mock_node.lookAt.call_args
        look_at_target = look_at_call[0][0]  # First positional argument
        
        # With positive side_offset, look target should shift left (negative X at yaw=0)
        # This frames the player to the right of screen
        self.assertNotEqual(look_at_target.x, 0.0, 
                           "Look-at target should shift horizontally with side_offset")
    
    def test_exploration_camera_minimum_distance(self):
        """Test that camera respects minimum distance even during collision."""
        mock_node = MagicMock()
        mock_node.getPos.return_value = LVector3f(0, -10, 5)
        
        cam = ExplorationCamera(mock_node)
        
        camera_state = CameraState(
            mode=CameraMode.EXPLORATION,
            yaw=0.0,
            pitch=0.0,
            distance=5.0,
            current_distance=0.5  # Very close (below min_distance)
        )
        
        ctx = CameraUpdateContext(
            camera_node=mock_node,
            camera_state=camera_state,
            target_position=LVector3f(0, 0, 0),
            player_velocity=LVector3f(0, 0, 0),
            mouse_delta=(0, 0),
            dt=0.016
        )
        
        cam.update(ctx)
        
        # Camera should have been positioned using current_distance
        mock_node.setPos.assert_called()
        set_pos_call = mock_node.setPos.call_args[0][0]
        
        # Verify camera is at some distance from target, not on top of player
        distance_from_target = set_pos_call.length()
        self.assertGreater(distance_from_target, 0.3, 
                          "Camera should maintain some distance from player")

if __name__ == '__main__':
    unittest.main()
