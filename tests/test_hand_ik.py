"""Tests for hand IK controller."""

import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock panda3d
from unittest.mock import MagicMock
from tests.test_utils.mock_panda import MockVector3, MockNodePath

mock_panda = MagicMock()
mock_core = MagicMock()

mock_core.NodePath = MockNodePath
mock_core.LVector3f = MockVector3
mock_core.LQuaternionf = MagicMock
sys.modules['panda3d'] = mock_panda
sys.modules['panda3d.core'] = mock_core

# Import after mocking
from engine.animation.hand_ik import HandIKController
from engine.animation.skeleton import HumanoidSkeleton


class TestHandIKController(unittest.TestCase):
    """Test hand IK for climbing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.skeleton = HumanoidSkeleton()
        self.skeleton.update_world_transforms()
        
        # Mock raycast that always hits a wall 0.5 units forward
        def mock_raycast(origin, direction):
            return MockVector3(
                origin.x + direction.x * 0.5,
                origin.y + direction.y * 0.5,
                origin.z + direction.z * 0.5
            )
        
        self.controller = HandIKController(raycast_callback=mock_raycast)
    
    def test_controller_initialization(self):
        """HandIKController should initialize with correct defaults."""
        self.assertIsNotNone(self.controller)
        self.assertFalse(self.controller.enabled)
        self.assertEqual(self.controller.reach_distance, 0.8)
        self.assertEqual(self.controller.hand_offset, 0.05)
    
    def test_disabled_controller_returns_empty_targets(self):
        """Disabled controller should return no IK targets."""
        targets = self.controller.update(
            self.skeleton,
            world_position=MockVector3(0, 0, 1),
            forward_direction=MockVector3(0, 1, 0),
            climbing=True
        )
        
        self.assertEqual(len(targets), 0)
    
    def test_enabled_controller_without_climbing_returns_empty(self):
        """Enabled controller without climbing state should return no targets."""
        self.controller.set_enabled(True)
        
        targets = self.controller.update(
            self.skeleton,
            world_position=MockVector3(0, 0, 1),
            forward_direction=MockVector3(0, 1, 0),
            climbing=False
        )
        
        self.assertEqual(len(targets), 0)
    
    def test_enabled_controller_with_climbing_generates_targets(self):
        """Enabled controller with climbing should generate hand IK targets."""
        self.controller.set_enabled(True)
        
        targets = self.controller.update(
            self.skeleton,
            world_position=MockVector3(0, 0, 1),
            forward_direction=MockVector3(0, 1, 0),
            climbing=True
        )
        
        # Should have targets for both hands
        self.assertIn("hand_left", targets)
        self.assertIn("hand_right", targets)
        
        # Targets should have correct bone names
        self.assertEqual(targets["hand_left"].bone_name, "hand_left")
        self.assertEqual(targets["hand_right"].bone_name, "hand_right")
        
        # Targets should have full weight
        self.assertEqual(targets["hand_left"].weight, 1.0)
        self.assertEqual(targets["hand_right"].weight, 1.0)
    
    def test_controller_caches_targets_between_updates(self):
        """Controller should cache targets based on update_interval."""
        self.controller.set_enabled(True)
        self.controller.update_interval = 2
        
        # First update (frame 1) - should compute
        targets1 = self.controller.update(
            self.skeleton,
            world_position=MockVector3(0, 0, 1),
            forward_direction=MockVector3(0, 1, 0),
            climbing=True
        )
        
        # Second update (frame 2) - should use cache
        targets2 = self.controller.update(
            self.skeleton,
            world_position=MockVector3(0, 0, 1),
            forward_direction=MockVector3(0, 1, 0),
            climbing=True
        )
        
        # Should be same cached targets
        self.assertEqual(targets1, targets2)
    
    def test_set_enabled_clears_cache(self):
        """Disabling controller should clear cached targets."""
        self.controller.set_enabled(True)
        
        # Generate some targets
        self.controller.update(
            self.skeleton,
            world_position=MockVector3(0, 0, 1),
            forward_direction=MockVector3(0, 1, 0),
            climbing=True
        )
        
        # Disable
        self.controller.set_enabled(False)
        
        # Cache should be cleared
        self.assertEqual(len(self.controller._last_targets), 0)
    
    def test_set_reach_distance(self):
        """set_reach_distance should update reach distance."""
        self.controller.set_reach_distance(1.5)
        self.assertEqual(self.controller.reach_distance, 1.5)
        
        # Should clamp to minimum
        self.controller.set_reach_distance(0.0)
        self.assertEqual(self.controller.reach_distance, 0.1)
    
    def test_unreachable_surface_no_targets(self):
        """Surfaces beyond reach distance should not generate targets."""
        # Mock raycast that hits far away
        def far_raycast(origin, direction):
            return MockVector3(
                origin.x + direction.x * 10.0,  # 10 units away
                origin.y + direction.y * 10.0,
                origin.z + direction.z * 10.0
            )
        
        controller = HandIKController(raycast_callback=far_raycast, reach_distance=0.8)
        controller.set_enabled(True)
        
        targets = controller.update(
            self.skeleton,
            world_position=MockVector3(0, 0, 1),
            forward_direction=MockVector3(0, 1, 0),
            climbing=True
        )
        
        # Should have no targets (surface too far)
        self.assertEqual(len(targets), 0)


if __name__ == '__main__':
    unittest.main()
