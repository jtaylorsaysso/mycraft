"""Tests for animation layer system."""

import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock panda3d
from unittest.mock import MagicMock

mock_panda = MagicMock()
mock_core = MagicMock()

class MockVector3:
    def __init__(self, x=0, y=0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, other):
        return MockVector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return MockVector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return MockVector3(self.x * other, self.y * other, self.z * other)
        return MockVector3(self.x * other.x, self.y * other.y, self.z * other.z)
    
    def __repr__(self):
        return f"MockVector3({self.x}, {self.y}, {self.z})"

mock_core.LVector3f = MockVector3
mock_core.LQuaternionf = MagicMock
mock_core.NodePath = MagicMock
sys.modules['panda3d'] = mock_panda
sys.modules['panda3d.core'] = mock_core

# Import after mocking
from engine.animation.layers import BoneMask, AnimationLayer, LayeredAnimator
from engine.animation.skeleton import HumanoidSkeleton
from engine.animation.core import Transform


class MockAnimationSource:
    """Mock animation source for testing."""
    
    def __init__(self, transforms=None):
        self.transforms = transforms or {}
        self.update_count = 0
    
    def update(self, dt, skeleton):
        self.update_count += 1
        return self.transforms.copy()


class TestBoneMask(unittest.TestCase):
    """Test bone mask filtering."""
    
    def test_full_body_affects_all_bones(self):
        """Full body mask should affect all bones."""
        mask = BoneMask.full_body()
        self.assertTrue(mask.affects_bone("hips"))
        self.assertTrue(mask.affects_bone("head"))
        self.assertTrue(mask.affects_bone("hand_left"))
        self.assertTrue(mask.affects_bone("foot_right"))
    
    def test_upper_body_affects_chest_and_above(self):
        """Upper body mask should affect chest, head, and arms."""
        mask = BoneMask.upper_body()
        self.assertTrue(mask.affects_bone("chest"))
        self.assertTrue(mask.affects_bone("head"))
        self.assertTrue(mask.affects_bone("upper_arm_left"))
        self.assertTrue(mask.affects_bone("hand_right"))
        self.assertFalse(mask.affects_bone("hips"))
        self.assertFalse(mask.affects_bone("thigh_left"))
        self.assertFalse(mask.affects_bone("foot_right"))
    
    def test_lower_body_affects_hips_and_below(self):
        """Lower body mask should affect hips, spine, and legs."""
        mask = BoneMask.lower_body()
        self.assertTrue(mask.affects_bone("hips"))
        self.assertTrue(mask.affects_bone("spine"))
        self.assertTrue(mask.affects_bone("thigh_left"))
        self.assertTrue(mask.affects_bone("foot_right"))
        self.assertFalse(mask.affects_bone("chest"))
        self.assertFalse(mask.affects_bone("head"))
        self.assertFalse(mask.affects_bone("hand_left"))
    
    def test_arms_mask_affects_only_arms(self):
        """Arms mask should affect only arm bones."""
        mask = BoneMask.arms()
        self.assertTrue(mask.affects_bone("upper_arm_left"))
        self.assertTrue(mask.affects_bone("forearm_right"))
        self.assertTrue(mask.affects_bone("hand_left"))
        self.assertFalse(mask.affects_bone("head"))
        self.assertFalse(mask.affects_bone("thigh_left"))
    
    def test_legs_mask_affects_only_legs(self):
        """Legs mask should affect only leg bones."""
        mask = BoneMask.legs()
        self.assertTrue(mask.affects_bone("thigh_left"))
        self.assertTrue(mask.affects_bone("shin_right"))
        self.assertTrue(mask.affects_bone("foot_left"))
        self.assertFalse(mask.affects_bone("head"))
        self.assertFalse(mask.affects_bone("hand_right"))


class TestAnimationLayer(unittest.TestCase):
    """Test animation layer functionality."""
    
    def test_layer_initialization(self):
        """Layer should initialize with correct defaults."""
        source = MockAnimationSource()
        layer = AnimationLayer(name="test", source=source)
        
        self.assertEqual(layer.name, "test")
        self.assertEqual(layer.weight, 1.0)
        self.assertEqual(layer.priority, 0)
        self.assertTrue(layer.enabled)
    
    def test_disabled_layer_returns_empty(self):
        """Disabled layer should return empty transforms."""
        transforms = {"bone1": Transform()}
        source = MockAnimationSource(transforms)
        layer = AnimationLayer(name="test", source=source, enabled=False)
        
        skeleton = HumanoidSkeleton()
        result = layer.get_transforms(0.1, skeleton)
        
        self.assertEqual(len(result), 0)
    
    def test_zero_weight_layer_returns_empty(self):
        """Zero weight layer should return empty transforms."""
        transforms = {"bone1": Transform()}
        source = MockAnimationSource(transforms)
        layer = AnimationLayer(name="test", source=source, weight=0.0)
        
        skeleton = HumanoidSkeleton()
        result = layer.get_transforms(0.1, skeleton)
        
        self.assertEqual(len(result), 0)


class TestLayeredAnimator(unittest.TestCase):
    """Test layered animator blending."""
    
    def test_animator_initialization(self):
        """Animator should initialize with skeleton."""
        skeleton = HumanoidSkeleton()
        animator = LayeredAnimator(skeleton)
        
        self.assertEqual(animator.skeleton, skeleton)
        self.assertEqual(len(animator.layers), 0)
    
    def test_add_layer(self):
        """Should be able to add layers."""
        skeleton = HumanoidSkeleton()
        animator = LayeredAnimator(skeleton)
        source = MockAnimationSource()
        
        layer = animator.add_layer("test", source, priority=5, weight=0.8)
        
        self.assertEqual(len(animator.layers), 1)
        self.assertEqual(layer.name, "test")
        self.assertEqual(layer.priority, 5)
        self.assertEqual(layer.weight, 0.8)
    
    def test_remove_layer(self):
        """Should be able to remove layers by name."""
        skeleton = HumanoidSkeleton()
        animator = LayeredAnimator(skeleton)
        
        animator.add_layer("layer1", MockAnimationSource())
        animator.add_layer("layer2", MockAnimationSource())
        
        self.assertEqual(len(animator.layers), 2)
        
        removed = animator.remove_layer("layer1")
        self.assertTrue(removed)
        self.assertEqual(len(animator.layers), 1)
        self.assertEqual(animator.layers[0].name, "layer2")
    
    def test_get_layer(self):
        """Should be able to retrieve layer by name."""
        skeleton = HumanoidSkeleton()
        animator = LayeredAnimator(skeleton)
        
        animator.add_layer("test", MockAnimationSource())
        layer = animator.get_layer("test")
        
        self.assertIsNotNone(layer)
        self.assertEqual(layer.name, "test")
    
    def test_set_layer_weight(self):
        """Should be able to modify layer weight."""
        skeleton = HumanoidSkeleton()
        animator = LayeredAnimator(skeleton)
        
        animator.add_layer("test", MockAnimationSource())
        animator.set_layer_weight("test", 0.5)
        
        layer = animator.get_layer("test")
        self.assertEqual(layer.weight, 0.5)
    
    def test_layers_sorted_by_priority(self):
        """Layers should be sorted by priority (low to high)."""
        skeleton = HumanoidSkeleton()
        animator = LayeredAnimator(skeleton)
        
        animator.add_layer("high", MockAnimationSource(), priority=10)
        animator.add_layer("low", MockAnimationSource(), priority=0)
        animator.add_layer("mid", MockAnimationSource(), priority=5)
        
        self.assertEqual(animator.layers[0].name, "low")
        self.assertEqual(animator.layers[1].name, "mid")
        self.assertEqual(animator.layers[2].name, "high")
    
    def test_single_layer_update(self):
        """Single layer should pass through its transforms."""
        skeleton = HumanoidSkeleton()
        animator = LayeredAnimator(skeleton)
        
        transform = Transform(position=MockVector3(1, 2, 3))
        source = MockAnimationSource({"hips": transform})
        animator.add_layer("test", source)
        
        pose = animator.update(0.1)
        
        self.assertIn("hips", pose)
        self.assertEqual(pose["hips"].position.x, 1)
        self.assertEqual(pose["hips"].position.y, 2)
        self.assertEqual(pose["hips"].position.z, 3)
    
    def test_bone_mask_filters_bones(self):
        """Bone mask should filter which bones are affected."""
        skeleton = HumanoidSkeleton()
        animator = LayeredAnimator(skeleton)
        
        # Layer affecting only upper body
        upper_transform = Transform(position=MockVector3(5, 5, 5))
        upper_source = MockAnimationSource({"chest": upper_transform, "thigh_left": upper_transform})
        animator.add_layer("upper", upper_source, mask=BoneMask.upper_body())
        
        pose = animator.update(0.1)
        
        # Chest should be affected (in upper body)
        self.assertIn("chest", pose)
        # Thigh should NOT be affected (not in upper body)
        self.assertNotIn("thigh_left", pose)
    
    def test_blend_two_layers(self):
        """Two layers with same weight should average transforms."""
        skeleton = HumanoidSkeleton()
        animator = LayeredAnimator(skeleton)
        
        # Layer 1: position (10, 0, 0)
        source1 = MockAnimationSource({"hips": Transform(position=MockVector3(10, 0, 0))})
        animator.add_layer("layer1", source1, weight=1.0)
        
        # Layer 2: position (0, 10, 0)
        source2 = MockAnimationSource({"hips": Transform(position=MockVector3(0, 10, 0))})
        animator.add_layer("layer2", source2, weight=1.0)
        
        pose = animator.update(0.1)
        
        # Should blend to (5, 5, 0)
        self.assertIn("hips", pose)
        self.assertAlmostEqual(pose["hips"].position.x, 5.0)
        self.assertAlmostEqual(pose["hips"].position.y, 5.0)
        self.assertAlmostEqual(pose["hips"].position.z, 0.0)


if __name__ == '__main__':
    unittest.main()
