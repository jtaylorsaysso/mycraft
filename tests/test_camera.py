
import unittest
from unittest.mock import MagicMock
from panda3d.core import LVector3f

from engine.rendering.camera import ThirdPersonCamera, FPSCamera

class TestCamera(unittest.TestCase):
    def test_third_person_camera_update(self):
        mock_node = MagicMock()
        mock_node.getPos.return_value = LVector3f(0, 0, 0)
        
        cam = ThirdPersonCamera(mock_node, None)
        cam.distance = 10.0
        
        # Initial State
        self.assertEqual(cam.yaw, 0.0)
        self.assertEqual(cam.pitch, -15.0)
        
        # Simulated Input: Move mouse right (positive DX)
        # Note: mouse_delta from InputManager is already normalized per-frame,
        # so we don't multiply by dt (it's framerate-independent already)
        dt = 0.016
        dx = 0.01  # Small normalized delta (like from InputManager)
        dy = 0.0
        
        cam.update(dx, dy, dt, LVector3f(0, 0, 0))
        
        # Check Yaw Update
        # yaw += dx * sensitivity (no dt multiplication)
        expected_yaw = 0.0 + (0.01 * 40.0)
        self.assertAlmostEqual(cam.yaw, expected_yaw, places=4)
        self.assertTrue(cam.yaw > 0)
        
        # Check Node Update
        mock_node.setPos.assert_called()
        mock_node.lookAt.assert_called()
        
    def test_fps_camera_update(self):
        mock_node = MagicMock()
        cam = FPSCamera(mock_node, None)
        
        cam.update(10.0, 5.0, 0.016)
        
        self.assertTrue(cam.yaw > 0)
        self.assertTrue(cam.pitch < 0) # Pitch is inverted (down is positive dy)
        mock_node.setHpr.assert_called()

if __name__ == '__main__':
    unittest.main()
