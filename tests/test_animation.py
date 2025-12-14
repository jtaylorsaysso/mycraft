"""
Tests for the procedural animation system.
"""
import unittest
from unittest.mock import MagicMock
import sys
import os
import math

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ----------------- MOCKS -----------------

class FakeVec3:
    """Fake Vec3 for testing."""
    def __init__(self, x=0, y=0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, other):
        return FakeVec3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return FakeVec3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return FakeVec3(self.x * other, self.y * other, self.z * other)
        return NotImplemented
    
    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return FakeVec3(self.x / other, self.y / other, self.z / other)
        return NotImplemented
    
    def length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)


class FakeEntity:
    """Fake Entity for testing animations without Ursina."""
    def __init__(self, **kwargs):
        self.position = kwargs.get('position', FakeVec3(0, 0, 0))
        if isinstance(self.position, tuple):
            self.position = FakeVec3(*self.position)
        
        self.rotation_x = kwargs.get('rotation_x', 0.0)
        self.rotation_y = kwargs.get('rotation_y', 0.0)
        self.rotation_z = kwargs.get('rotation_z', 0.0)
        self.scale = kwargs.get('scale', 1.0)
        self.y = kwargs.get('y', 0.0)
        self.origin_y = kwargs.get('origin_y', 0.0)
        self.parent = kwargs.get('parent', None)
        self.model = kwargs.get('model', None)
        self.color = kwargs.get('color', None)
        self.children = []
        
        if self.parent and hasattr(self.parent, 'children'):
            self.parent.children.append(self)
    
    def animate(self, attr, value, duration=1.0, **kwargs):
        """Mock animate - instantly sets value for testing."""
        setattr(self, attr, value)


# Mock ursina module
mock_ursina = MagicMock()
mock_ursina.Entity = FakeEntity
mock_ursina.Vec3 = FakeVec3
mock_ursina.color = MagicMock()
mock_ursina.color.azure = "azure"
mock_ursina.color.rgb = lambda r, g, b: (r, g, b)

# Mock time
mock_time = MagicMock()
mock_time.dt = 0.016
mock_ursina.time = mock_time

sys.modules['ursina'] = mock_ursina

# ----------------- IMPORT AFTER MOCKING -----------------

from engine.animation import AnimationState, AnimatedMannequin, AnimationController


# ----------------- TESTS -----------------

class TestAnimationState(unittest.TestCase):
    """Test AnimationState enum."""
    
    def test_all_states_exist(self):
        """Verify all expected states are defined."""
        self.assertIsNotNone(AnimationState.IDLE)
        self.assertIsNotNone(AnimationState.WALKING)
        self.assertIsNotNone(AnimationState.JUMPING)
        self.assertIsNotNone(AnimationState.FALLING)
        self.assertIsNotNone(AnimationState.LANDING)
    
    def test_states_are_unique(self):
        """Verify all states have unique values."""
        states = [s.value for s in AnimationState]
        self.assertEqual(len(states), len(set(states)))


class TestAnimatedMannequin(unittest.TestCase):
    """Test AnimatedMannequin class."""
    
    def setUp(self):
        self.mannequin = AnimatedMannequin()
    
    def test_initialization(self):
        """Test mannequin initializes with correct attributes."""
        self.assertEqual(self.mannequin._walk_phase, 0.0)
        self.assertEqual(self.mannequin._idle_time, 0.0)
    
    def test_has_body_parts(self):
        """Test mannequin has all expected body part attributes."""
        self.assertTrue(hasattr(self.mannequin, 'head'))
        self.assertTrue(hasattr(self.mannequin, 'torso'))
        self.assertTrue(hasattr(self.mannequin, 'right_arm'))
        self.assertTrue(hasattr(self.mannequin, 'left_arm'))
        self.assertTrue(hasattr(self.mannequin, 'right_leg'))
        self.assertTrue(hasattr(self.mannequin, 'left_leg'))
    
    def test_has_pivot_points(self):
        """Test mannequin has pivot points for limb animation."""
        self.assertTrue(hasattr(self.mannequin, 'right_arm_pivot'))
        self.assertTrue(hasattr(self.mannequin, 'left_arm_pivot'))
        self.assertTrue(hasattr(self.mannequin, 'right_leg_pivot'))
        self.assertTrue(hasattr(self.mannequin, 'left_leg_pivot'))
    
    def test_reset_pose(self):
        """Test reset_pose resets walk phase."""
        self.mannequin._walk_phase = 1.5
        self.mannequin.reset_pose()
        self.assertEqual(self.mannequin._walk_phase, 0.0)
    
    def test_body_parts_are_entities(self):
        """Test all body parts are FakeEntity instances."""
        self.assertIsInstance(self.mannequin.head, FakeEntity)
        self.assertIsInstance(self.mannequin.torso, FakeEntity)
        self.assertIsInstance(self.mannequin.right_arm, FakeEntity)
        self.assertIsInstance(self.mannequin.left_arm, FakeEntity)
        self.assertIsInstance(self.mannequin.right_leg, FakeEntity)
        self.assertIsInstance(self.mannequin.left_leg, FakeEntity)


class TestAnimationController(unittest.TestCase):
    """Test AnimationController state machine."""
    
    def setUp(self):
        self.mannequin = AnimatedMannequin()
        self.controller = AnimationController(self.mannequin)
    
    def test_initial_state(self):
        """Test controller starts in IDLE state."""
        self.assertEqual(self.controller.current_state, AnimationState.IDLE)
    
    def test_set_state_changes_state(self):
        """Test set_state transitions to new state."""
        self.controller.set_state(AnimationState.WALKING)
        self.assertEqual(self.controller.current_state, AnimationState.WALKING)
    
    def test_set_same_state_no_op(self):
        """Test setting same state doesn't reset state time."""
        self.controller.set_state(AnimationState.WALKING)
        self.controller._state_time = 1.0
        self.controller.set_state(AnimationState.WALKING)
        self.assertEqual(self.controller._state_time, 1.0)
    
    def test_update_detects_walking(self):
        """Test update transitions to WALKING when moving."""
        velocity = FakeVec3(3.0, 0, 0)
        self.controller.update(0.016, velocity, grounded=True)
        self.assertEqual(self.controller.current_state, AnimationState.WALKING)
    
    def test_update_detects_idle(self):
        """Test update stays/transitions to IDLE when still."""
        velocity = FakeVec3(0.1, 0, 0)  # Very slow
        self.controller.update(0.016, velocity, grounded=True)
        self.assertEqual(self.controller.current_state, AnimationState.IDLE)
    
    def test_update_detects_jumping(self):
        """Test update transitions to JUMPING when rising."""
        velocity = FakeVec3(0, 5.0, 0)  # Moving up
        self.controller.update(0.016, velocity, grounded=False)
        self.assertEqual(self.controller.current_state, AnimationState.JUMPING)
    
    def test_update_detects_falling(self):
        """Test update transitions to FALLING when descending."""
        velocity = FakeVec3(0, -5.0, 0)  # Moving down
        self.controller.update(0.016, velocity, grounded=False)
        self.assertEqual(self.controller.current_state, AnimationState.FALLING)
    
    def test_landing_after_falling(self):
        """Test landing state after falling and hitting ground."""
        # Start falling
        velocity = FakeVec3(0, -5.0, 0)
        self.controller.update(0.016, velocity, grounded=False)
        self.assertEqual(self.controller.current_state, AnimationState.FALLING)
        
        # Hit ground
        velocity = FakeVec3(0, 0, 0)
        self.controller.update(0.016, velocity, grounded=True)
        self.assertEqual(self.controller.current_state, AnimationState.LANDING)
    
    def test_landing_transitions_to_idle(self):
        """Test landing state transitions to idle after duration."""
        # Force into landing state
        self.controller.set_state(AnimationState.LANDING)
        
        # Wait for landing duration to pass
        velocity = FakeVec3(0, 0, 0)
        for _ in range(20):  # 20 * 0.016 = 0.32s > landing_duration (0.15s)
            self.controller.update(0.016, velocity, grounded=True)
        
        self.assertEqual(self.controller.current_state, AnimationState.IDLE)
    
    def test_walk_phase_advances(self):
        """Test walk phase advances when walking."""
        initial_phase = self.mannequin._walk_phase
        
        # Force walking state and run walk animation
        self.controller.set_state(AnimationState.WALKING)
        self.controller._update_procedural_animation(0.1, speed=3.0)
        
        self.assertGreater(self.mannequin._walk_phase, initial_phase)


class TestAnimationStateTransitions(unittest.TestCase):
    """Integration tests for animation state machine transitions."""
    
    def setUp(self):
        self.mannequin = AnimatedMannequin()
        self.controller = AnimationController(self.mannequin)
    
    def test_full_jump_cycle(self):
        """Test complete jump cycle: idle -> jumping -> falling -> landing -> idle."""
        # Start idle
        self.assertEqual(self.controller.current_state, AnimationState.IDLE)
        
        # Jump (moving up, not grounded)
        self.controller.update(0.016, FakeVec3(0, 5.0, 0), grounded=False)
        self.assertEqual(self.controller.current_state, AnimationState.JUMPING)
        
        # Fall (moving down)
        self.controller.update(0.016, FakeVec3(0, -3.0, 0), grounded=False)
        self.assertEqual(self.controller.current_state, AnimationState.FALLING)
        
        # Land
        self.controller.update(0.016, FakeVec3(0, 0, 0), grounded=True)
        self.assertEqual(self.controller.current_state, AnimationState.LANDING)
        
        # Wait for landing to finish
        for _ in range(20):
            self.controller.update(0.016, FakeVec3(0, 0, 0), grounded=True)
        self.assertEqual(self.controller.current_state, AnimationState.IDLE)
    
    def test_walking_while_landing_skips_idle(self):
        """Test that walking during landing transitions to walking."""
        # Force landing state
        self.controller.set_state(AnimationState.LANDING)
        
        # Walk during landing wait
        for _ in range(20):
            self.controller.update(0.016, FakeVec3(3.0, 0, 0), grounded=True)
        
        # Should transition to WALKING, not IDLE
        self.assertEqual(self.controller.current_state, AnimationState.WALKING)
    
    def test_arm_swing_during_walk(self):
        """Test that arms swing during walk animation."""
        # Start walking
        self.controller.set_state(AnimationState.WALKING)
        
        # Run a few walk updates
        for _ in range(10):
            self.controller._update_procedural_animation(0.05, speed=3.0)
        
        # Arms should have rotated from neutral position
        # At least one arm should be rotated
        arm_rotated = (
            abs(self.mannequin.right_arm_pivot.rotation_x) > 1 or
            abs(self.mannequin.left_arm_pivot.rotation_x) > 1
        )
        self.assertTrue(arm_rotated, "Arms should swing during walk animation")


if __name__ == '__main__':
    unittest.main()
