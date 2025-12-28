"""Tests for player physics via GroundMovementMechanic.

Tests the mechanics-based architecture directly, which is cleaner than
testing the full PlayerControlSystem coordinator.
"""

import sys
from unittest.mock import MagicMock, patch

# Mock panda3d before importing anything else
import sys
from unittest.mock import MagicMock
from tests.test_utils.mock_panda import MockVector3, MockNodePath

mock_panda = MagicMock()
mock_core = MagicMock()

mock_core.LVector3f = MockVector3
mock_core.NodePath = MockNodePath
mock_core.WindowProperties = MagicMock()
mock_core.ModifierButtons = MagicMock()
mock_core.CollisionHandlerQueue.return_value.getNumEntries.return_value = 0
mock_core.BitMask32.bit.return_value = 1
mock_core.BitMask32.allOff.return_value = 0
mock_core.CollisionTraverser = MagicMock()
mock_panda.core = mock_core
sys.modules['panda3d'] = mock_panda
sys.modules['panda3d.core'] = mock_core

import unittest
from engine.physics import KinematicState, apply_gravity, apply_horizontal_acceleration
from engine.physics.constants import GRAVITY, WATER_DRAG


class TestKinematicPhysics(unittest.TestCase):
    """Test kinematic physics functions directly."""
    
    def test_gravity_accelerates_downward(self):
        """Verify gravity accelerates entity downwards."""
        state = KinematicState()
        state.velocity_z = 0
        
        # Apply gravity
        dt = 0.1
        apply_gravity(state, dt, gravity=GRAVITY)
        
        # Should have negative velocity (falling)
        self.assertLess(state.velocity_z, 0)
        # With gravity of -20 and dt of 0.1, we expect -2.0 velocity
        self.assertAlmostEqual(state.velocity_z, -2.0, delta=0.1)
    
    def test_water_gravity_is_reduced(self):
        """Verify water gravity is much lower than normal."""
        WATER_GRAVITY = -2.0  # From PlayerControlSystem
        
        # In air
        air_state = KinematicState()
        apply_gravity(air_state, 0.1, gravity=GRAVITY)
        
        # In water
        water_state = KinematicState()
        apply_gravity(water_state, 0.1, gravity=WATER_GRAVITY)
        
        # Water velocity should be higher (less negative) than air
        self.assertGreater(water_state.velocity_z, air_state.velocity_z)
        # Air: -2.0, Water: -0.2
        self.assertAlmostEqual(water_state.velocity_z, -0.2, delta=0.1)
    
    def test_horizontal_acceleration_grounded(self):
        """Test horizontal acceleration when grounded."""
        state = KinematicState()
        state.grounded = True
        state.velocity_x = 0
        state.velocity_y = 0
        
        # Accelerate forward (in Y direction for Panda3D)
        target = (0, 5.0)  # Target velocity
        dt = 0.1
        apply_horizontal_acceleration(state, target, dt, grounded=True)
        
        # Should have positive Y velocity
        self.assertGreater(state.velocity_y, 0)
    
    def test_horizontal_friction_when_stopped(self):
        """Test friction slows horizontal movement when no input."""
        state = KinematicState()
        state.grounded = True
        state.velocity_x = 5.0
        state.velocity_y = 0
        
        # No target velocity (stopped input)
        target = (0, 0)
        dt = 0.1
        apply_horizontal_acceleration(state, target, dt, grounded=True)
        
        # Should slow down
        self.assertLess(state.velocity_x, 5.0)
    
    def test_air_control_is_reduced(self):
        """Test that air control is weaker than ground control."""
        # Ground state
        ground_state = KinematicState()
        ground_state.grounded = True
        ground_state.velocity_x = 0
        
        # Air state
        air_state = KinematicState()
        air_state.grounded = False
        air_state.velocity_x = 0
        
        # Same input for both
        target = (5.0, 0)
        dt = 0.1
        
        apply_horizontal_acceleration(ground_state, target, dt, grounded=True)
        apply_horizontal_acceleration(air_state, target, dt, grounded=False)
        
        # Ground should accelerate more than air
        self.assertGreater(ground_state.velocity_x, air_state.velocity_x)


class TestWaterPhysics(unittest.TestCase):
    """Test water-specific physics behavior."""
    
    def test_water_drag_slows_movement(self):
        """Test that water drag slows horizontal velocity."""
        velocity_x = 20.0
        dt = 0.1
        
        # Apply water drag formula: vel *= max(0, 1 - WATER_DRAG * dt)
        new_velocity = velocity_x * max(0, 1 - WATER_DRAG * dt)
        
        # Should be slower
        self.assertLess(new_velocity, velocity_x)
        # With WATER_DRAG=2.0 and dt=0.1: 20 * 0.8 = 16
        self.assertAlmostEqual(new_velocity, 16.0, delta=1.0)


class TestJumpMechanics(unittest.TestCase):
    """Test jump-related physics."""
    
    def test_jump_applies_upward_velocity(self):
        """Test jumping applies correct upward velocity."""
        from engine.physics import perform_jump
        from engine.physics.constants import JUMP_VELOCITY
        
        state = KinematicState()
        state.grounded = True
        state.velocity_z = 0
        
        perform_jump(state, JUMP_VELOCITY)
        
        # Should have positive Z velocity
        self.assertGreater(state.velocity_z, 0)
        self.assertEqual(state.velocity_z, JUMP_VELOCITY)
    
    def test_coyote_time_allows_late_jump(self):
        """Test coyote time allows jumping shortly after leaving ground."""
        from engine.physics import register_jump_press, can_consume_jump
        
        state = KinematicState()
        state.grounded = False
        state.coyote_time = 0.05  # Just left ground
        state.jump_buffered = False
        
        # Press jump
        register_jump_press(state)
        
        # Should be able to jump (coyote time active)
        self.assertTrue(can_consume_jump(state))
    
    def test_jump_buffer_works(self):
        """Test jump buffer allows early jump press."""
        from engine.physics import register_jump_press, can_consume_jump
        
        state = KinematicState()
        state.grounded = True
        state.coyote_time = 0
        state.jump_buffered = False
        state.jump_buffer_time = 0
        
        # Press jump
        register_jump_press(state)
        
        # Should be able to jump
        self.assertTrue(can_consume_jump(state))


if __name__ == '__main__':
    unittest.main()
