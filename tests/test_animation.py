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

# Mock panda3d before importing anything else
import sys
from unittest.mock import MagicMock
from tests.test_utils.mock_panda import MockVector3, MockNodePath

mock_panda = MagicMock()
mock_core = MagicMock()

# Mock CardMaker for cube generation
class MockCardMaker:
    def __init__(self, name):
        self.name = name
    def setFrame(self, *args):
        pass
    def generate(self):
        return MagicMock()

mock_core.NodePath = MockNodePath
mock_core.LVector3f = MockVector3
mock_core.GeomNode = MagicMock
mock_core.CardMaker = MockCardMaker
mock_panda.core = mock_core
sys.modules['panda3d'] = mock_panda
sys.modules['panda3d.core'] = mock_core

# Mock direct.interval
mock_direct = MagicMock()
sys.modules['direct'] = mock_direct
sys.modules['direct.interval'] = MagicMock()
sys.modules['direct.interval.IntervalGlobal'] = MagicMock()

# ----------------- IMPORT AFTER MOCKING -----------------

from engine.animation.mannequin import AnimationState, AnimationController, AnimatedMannequin


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
        # Create a mock parent node
        self.parent_node = MockNodePath("parent")
        self.mannequin = AnimatedMannequin(self.parent_node)
    
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
        """Test all body parts are MockNodePath instances."""
        # In the Panda3D implementation, body parts are NodePaths created by _create_cube
        # which returns nodes attached to the mannequin hierarchy
        self.assertIsInstance(self.mannequin.head, MockNodePath)
        self.assertIsInstance(self.mannequin.torso, MockNodePath)
        self.assertIsInstance(self.mannequin.right_arm, MockNodePath)
        self.assertIsInstance(self.mannequin.left_arm, MockNodePath)
        self.assertIsInstance(self.mannequin.right_leg, MockNodePath)
        self.assertIsInstance(self.mannequin.left_leg, MockNodePath)


class TestAnimationController(unittest.TestCase):
    """Test AnimationController state machine."""
    
    def setUp(self):
        parent_node = MockNodePath("parent")
        self.mannequin = AnimatedMannequin(parent_node)
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
        velocity = MockVector3(3.0, 0, 0)
        self.controller.update(0.016, velocity, grounded=True)
        self.assertEqual(self.controller.current_state, AnimationState.WALKING)
    
    def test_update_detects_idle(self):
        """Test update stays/transitions to IDLE when still."""
        velocity = MockVector3(0.1, 0, 0)  # Very slow
        self.controller.update(0.016, velocity, grounded=True)
        self.assertEqual(self.controller.current_state, AnimationState.IDLE)
    
    def test_update_detects_jumping(self):
        """Test update transitions to JUMPING when rising."""
        velocity = MockVector3(0, 0, 5.0)  # Moving up (Z is up in Panda3D)
        self.controller.update(0.016, velocity, grounded=False)
        self.assertEqual(self.controller.current_state, AnimationState.JUMPING)
    
    def test_update_detects_falling(self):
        """Test update transitions to FALLING when descending."""
        velocity = MockVector3(0, 0, -5.0)  # Moving down
        self.controller.update(0.016, velocity, grounded=False)
        self.assertEqual(self.controller.current_state, AnimationState.FALLING)
    
    def test_landing_after_falling(self):
        """Test landing state after falling and hitting ground."""
        # Start falling
        velocity = MockVector3(0, 0, -5.0)
        self.controller.update(0.016, velocity, grounded=False)
        self.assertEqual(self.controller.current_state, AnimationState.FALLING)
        
        # Hit ground
        velocity = MockVector3(0, 0, 0)
        self.controller.update(0.016, velocity, grounded=True)
        self.assertEqual(self.controller.current_state, AnimationState.LANDING)
    
    def test_landing_transitions_to_idle(self):
        """Test landing state transitions to idle after duration."""
        # Force into landing state
        self.controller.set_state(AnimationState.LANDING)
        
        # Wait for landing duration to pass
        velocity = MockVector3(0, 0, 0)
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
        parent_node = MockNodePath("parent")
        self.mannequin = AnimatedMannequin(parent_node)
        self.controller = AnimationController(self.mannequin)
    
    def test_full_jump_cycle(self):
        """Test complete jump cycle: idle -> jumping -> falling -> landing -> idle."""
        # Start idle
        self.assertEqual(self.controller.current_state, AnimationState.IDLE)
        
        # Jump (moving up, not grounded)
        self.controller.update(0.016, MockVector3(0, 0, 5.0), grounded=False)
        self.assertEqual(self.controller.current_state, AnimationState.JUMPING)
        
        # Fall (moving down)
        self.controller.update(0.016, MockVector3(0, 0, -3.0), grounded=False)
        self.assertEqual(self.controller.current_state, AnimationState.FALLING)
        
        # Land
        self.controller.update(0.016, MockVector3(0, 0, 0), grounded=True)
        self.assertEqual(self.controller.current_state, AnimationState.LANDING)
        
        # Wait for landing to finish
        for _ in range(20):
            self.controller.update(0.016, MockVector3(0, 0, 0), grounded=True)
        self.assertEqual(self.controller.current_state, AnimationState.IDLE)
    
    def test_walking_while_landing_skips_idle(self):
        """Test that walking during landing transitions to walking."""
        # Force landing state
        self.controller.set_state(AnimationState.LANDING)
        
        # Walk during landing wait
        for _ in range(20):
            self.controller.update(0.016, MockVector3(3.0, 0, 0), grounded=True)
        
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
        # Check that at least one arm pivot has non-zero pitch (hpr.y in our mock)
        arm_rotated = (
            abs(self.mannequin.right_arm_pivot.hpr.y) > 1 or
            abs(self.mannequin.left_arm_pivot.hpr.y) > 1
        )
        self.assertTrue(arm_rotated, "Arms should swing during walk animation")



if __name__ == '__main__':
    unittest.main()
