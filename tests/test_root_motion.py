"""Tests for root motion system."""

import unittest
import sys
import os
import math

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
    
    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return MockVector3(self.x / other, self.y / other, self.z / other)
        return MockVector3(self.x / other.x, self.y / other.y, self.z / other.z)
    
    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
    
    def __repr__(self):
        return f"MockVector3({self.x}, {self.y}, {self.z})"

mock_core.LVector3f = MockVector3
mock_core.LQuaternionf = MagicMock
mock_core.NodePath = MagicMock
sys.modules['panda3d'] = mock_panda
sys.modules['panda3d.core'] = mock_core

# Import after mocking
from engine.animation.root_motion import (
    RootMotionCurve,
    RootMotionClip,
    RootMotionApplicator,
    add_root_motion_to_attack
)
from engine.animation.core import AnimationClip, Keyframe, Transform


class TestRootMotionCurve(unittest.TestCase):
    """Test root motion curve functionality."""
    
    def test_curve_initialization(self):
        """Curve should initialize empty."""
        curve = RootMotionCurve()
        self.assertEqual(len(curve.samples), 0)
    
    def test_add_sample(self):
        """Should be able to add samples."""
        curve = RootMotionCurve()
        curve.add_sample(0.0, MockVector3(1, 0, 0))
        curve.add_sample(0.5, MockVector3(1, 0, 0))
        
        self.assertEqual(len(curve.samples), 2)
    
    def test_samples_sorted_by_time(self):
        """Samples should be sorted by time."""
        curve = RootMotionCurve()
        curve.add_sample(0.5, MockVector3(1, 0, 0))
        curve.add_sample(0.0, MockVector3(1, 0, 0))
        curve.add_sample(0.25, MockVector3(1, 0, 0))
        
        self.assertEqual(curve.samples[0][0], 0.0)
        self.assertEqual(curve.samples[1][0], 0.25)
        self.assertEqual(curve.samples[2][0], 0.5)
    
    def test_get_delta_accumulates_motion(self):
        """get_delta should accumulate motion between times."""
        curve = RootMotionCurve()
        curve.add_sample(0.0, MockVector3(1, 0, 0))
        curve.add_sample(0.1, MockVector3(1, 0, 0))
        curve.add_sample(0.2, MockVector3(1, 0, 0))
        
        delta = curve.get_delta(0.0, 0.2)
        
        # Should accumulate all three samples
        self.assertAlmostEqual(delta.x, 3.0)
        self.assertAlmostEqual(delta.y, 0.0)
    
    def test_get_delta_partial_range(self):
        """get_delta should only include samples in range."""
        curve = RootMotionCurve()
        curve.add_sample(0.0, MockVector3(1, 0, 0))
        curve.add_sample(0.1, MockVector3(1, 0, 0))
        curve.add_sample(0.2, MockVector3(1, 0, 0))
        curve.add_sample(0.3, MockVector3(1, 0, 0))
        
        delta = curve.get_delta(0.1, 0.2)
        
        # Should only include samples at 0.1 and 0.2
        self.assertAlmostEqual(delta.x, 2.0)
    
    def test_linear_curve(self):
        """Linear curve should distribute motion evenly."""
        total = MockVector3(10, 0, 0)
        curve = RootMotionCurve.linear(total, duration=1.0, samples=10)
        
        self.assertEqual(len(curve.samples), 10)
        
        # Each sample should have 1/10th of total
        for _, delta in curve.samples:
            self.assertAlmostEqual(delta.x, 1.0)
    
    def test_attack_lunge_curve(self):
        """Attack lunge should create smooth acceleration curve."""
        curve = RootMotionCurve.attack_lunge(forward_distance=5.0, duration=0.5)
        
        # Should have samples
        self.assertGreater(len(curve.samples), 0)
        
        # Total displacement should approximately equal forward_distance
        # (small precision loss from sine curve sampling)
        total_delta = curve.get_delta(0.0, 0.5)
        self.assertAlmostEqual(total_delta.y, 5.0, delta=0.1)


class TestRootMotionClip(unittest.TestCase):
    """Test root motion clip functionality."""
    
    def test_clip_with_root_motion(self):
        """Clip should store and return root motion."""
        curve = RootMotionCurve.linear(MockVector3(0, 5, 0), duration=1.0)
        clip = RootMotionClip(
            name="test",
            duration=1.0,
            keyframes=[],
            root_motion=curve
        )
        
        delta = clip.get_root_delta(0.0, 1.0)
        self.assertAlmostEqual(delta.y, 5.0, places=1)
    
    def test_clip_without_root_motion(self):
        """Clip without root motion should return zero delta."""
        clip = RootMotionClip(
            name="test",
            duration=1.0,
            keyframes=[]
        )
        
        delta = clip.get_root_delta(0.0, 1.0)
        self.assertEqual(delta.x, 0.0)
        self.assertEqual(delta.y, 0.0)
        self.assertEqual(delta.z, 0.0)


class TestRootMotionApplicator(unittest.TestCase):
    """Test root motion application to kinematic state."""
    
    def test_applicator_initialization(self):
        """Applicator should initialize with defaults."""
        applicator = RootMotionApplicator()
        self.assertTrue(applicator.enabled)
        self.assertEqual(applicator.scale, 1.0)
    
    def test_extract_and_apply(self):
        """Should extract motion and apply to kinematic state."""
        # Create clip with forward motion
        curve = RootMotionCurve.linear(MockVector3(0, 2, 0), duration=1.0, samples=10)
        clip = RootMotionClip(
            name="test",
            duration=1.0,
            keyframes=[],
            root_motion=curve
        )
        
        # Mock kinematic state
        class MockKinematicState:
            def __init__(self):
                self.position = MockVector3(0, 0, 0)
        
        kinematic = MockKinematicState()
        applicator = RootMotionApplicator()
        
        # Apply motion for 0.1 seconds
        delta = applicator.extract_and_apply(
            clip,
            current_time=0.1,
            dt=0.1,
            kinematic_state=kinematic,
            character_rotation=0.0
        )
        
        # Should have moved forward
        self.assertGreater(kinematic.position.y, 0.0)
    
    def test_disabled_applicator_no_motion(self):
        """Disabled applicator should not apply motion."""
        curve = RootMotionCurve.linear(MockVector3(0, 2, 0), duration=1.0)
        clip = RootMotionClip(
            name="test",
            duration=1.0,
            keyframes=[],
            root_motion=curve
        )
        
        class MockKinematicState:
            def __init__(self):
                self.position = MockVector3(0, 0, 0)
        
        kinematic = MockKinematicState()
        applicator = RootMotionApplicator()
        applicator.set_enabled(False)
        
        applicator.extract_and_apply(
            clip,
            current_time=0.1,
            dt=0.1,
            kinematic_state=kinematic,
            character_rotation=0.0
        )
        
        # Should not have moved
        self.assertEqual(kinematic.position.y, 0.0)
    
    def test_scale_affects_motion(self):
        """Scale should multiply motion delta."""
        curve = RootMotionCurve.linear(MockVector3(0, 10, 0), duration=1.0, samples=10)
        clip = RootMotionClip(
            name="test",
            duration=1.0,
            keyframes=[],
            root_motion=curve
        )
        
        class MockKinematicState:
            def __init__(self):
                self.position = MockVector3(0, 0, 0)
        
        kinematic = MockKinematicState()
        applicator = RootMotionApplicator()
        applicator.set_scale(0.5)  # Half speed
        
        applicator.extract_and_apply(
            clip,
            current_time=0.1,
            dt=0.1,
            kinematic_state=kinematic,
            character_rotation=0.0
        )
        
        # Motion should be scaled (half speed means less distance)
        # With 0.5 scale, should move approximately 0.5 units instead of 1.0
        self.assertLess(kinematic.position.y, 0.9)  # Less than full speed


class TestRootMotionHelpers(unittest.TestCase):
    """Test helper functions."""
    
    def test_add_root_motion_to_attack(self):
        """Should convert AnimationClip to RootMotionClip."""
        original = AnimationClip(
            name="attack",
            duration=0.5,
            keyframes=[],
            looping=False
        )
        
        with_motion = add_root_motion_to_attack(
            original,
            forward_distance=2.0,
            motion_type="lunge"
        )
        
        self.assertIsInstance(with_motion, RootMotionClip)
        self.assertIsNotNone(with_motion.root_motion)
        self.assertEqual(with_motion.name, "attack")
        self.assertEqual(with_motion.duration, 0.5)


if __name__ == '__main__':
    unittest.main()
