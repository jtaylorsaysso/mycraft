"""
Tests for SymmetryController.
"""

import pytest
from panda3d.core import LVector3f

from engine.animation.skeleton import HumanoidSkeleton
from engine.editor.tools.common.symmetry_controller import SymmetryController


class TestSymmetryController:
    """Tests for bilateral symmetry mirroring."""
    
    @pytest.fixture
    def skeleton(self):
        """Create a test skeleton."""
        return HumanoidSkeleton()
        
    @pytest.fixture
    def controller(self, skeleton):
        """Create a SymmetryController."""
        return SymmetryController(skeleton)
        
    def test_get_mirror_bone(self, controller):
        """Test bone pairing lookup."""
        assert controller.get_mirror_bone("upper_arm_left") == "upper_arm_right"
        assert controller.get_mirror_bone("upper_arm_right") == "upper_arm_left"
        assert controller.get_mirror_bone("thigh_left") == "thigh_right"
        assert controller.get_mirror_bone("hips") is None  # Unpaired bone
        assert controller.get_mirror_bone("spine") is None
        
    def test_mirror_position(self, controller, skeleton):
        """Test position mirroring across X axis."""
        left_bone = skeleton.get_bone("upper_arm_left")
        right_bone = skeleton.get_bone("upper_arm_right")
        
        # Set left position
        test_pos = LVector3f(1.0, 2.0, 3.0)
        left_bone.local_transform.position = test_pos
        
        # Mirror to right
        controller.mirror_position("upper_arm_left", test_pos)
        
        # Right should have X flipped
        assert abs(right_bone.local_transform.position.x - (-1.0)) < 0.001
        assert abs(right_bone.local_transform.position.y - 2.0) < 0.001
        assert abs(right_bone.local_transform.position.z - 3.0) < 0.001
        
    def test_mirror_rotation(self, controller, skeleton):
        """Test rotation mirroring (heading inverted)."""
        left_bone = skeleton.get_bone("forearm_left")
        right_bone = skeleton.get_bone("forearm_right")
        
        # Set left rotation (H, P, R)
        test_rot = LVector3f(45.0, 30.0, 15.0)
        left_bone.local_transform.rotation = test_rot
        
        # Mirror to right
        controller.mirror_rotation("forearm_left", test_rot)
        
        # Right should have heading inverted
        assert abs(right_bone.local_transform.rotation.x - (-45.0)) < 0.001
        assert abs(right_bone.local_transform.rotation.y - 30.0) < 0.001
        assert abs(right_bone.local_transform.rotation.z - 15.0) < 0.001
        
    def test_mirror_length(self, controller, skeleton):
        """Test length mirroring (same value)."""
        left_bone = skeleton.get_bone("thigh_left")
        right_bone = skeleton.get_bone("thigh_right")
        
        # Set left length
        test_length = 0.75
        left_bone.length = test_length
        
        # Mirror to right
        controller.mirror_length("thigh_left", test_length)
        
        # Right should have same length
        assert abs(right_bone.length - test_length) < 0.001
        
    def test_toggle_enabled(self, controller, skeleton):
        """Test enabling/disabling symmetry."""
        left_bone = skeleton.get_bone("hand_left")
        right_bone = skeleton.get_bone("hand_right")
        
        # Disable symmetry
        controller.set_enabled(False)
        
        # Try to mirror - should not affect right bone
        original_pos = LVector3f(right_bone.local_transform.position)
        controller.mirror_position("hand_left", LVector3f(5.0, 5.0, 5.0))
        
        # Right bone should be unchanged
        assert abs(right_bone.local_transform.position.x - original_pos.x) < 0.001
        assert abs(right_bone.local_transform.position.y - original_pos.y) < 0.001
        assert abs(right_bone.local_transform.position.z - original_pos.z) < 0.001
        
        # Re-enable and try again
        controller.set_enabled(True)
        controller.mirror_position("hand_left", LVector3f(5.0, 5.0, 5.0))
        
        # Now it should mirror
        assert abs(right_bone.local_transform.position.x - (-5.0)) < 0.001
        
    def test_mirror_transform_all(self, controller, skeleton):
        """Test mirroring all transform components at once."""
        left_bone = skeleton.get_bone("shin_left")
        right_bone = skeleton.get_bone("shin_right")
        
        # Set all left bone properties
        left_bone.local_transform.position = LVector3f(2.0, 1.0, 0.5)
        left_bone.local_transform.rotation = LVector3f(90.0, 45.0, 0.0)
        left_bone.length = 0.6
        
        # Mirror all
        controller.mirror_transform("shin_left")
        
        # Check all mirrored correctly
        assert abs(right_bone.local_transform.position.x - (-2.0)) < 0.001
        assert abs(right_bone.local_transform.rotation.x - (-90.0)) < 0.001
        assert abs(right_bone.length - 0.6) < 0.001
