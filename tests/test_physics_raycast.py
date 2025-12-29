"""Tests for raycast-based ground detection in physics system."""

import unittest
from unittest.mock import MagicMock
from tests.test_utils.mock_panda import MockVector3, MockNodePath
from engine.physics import (
    KinematicState,
    apply_gravity,
    integrate_movement,
    raycast_ground_height,
)


class MockEntity:
    """Mock entity for testing without Panda3D dependency."""
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class TestPhysicsRaycast(unittest.TestCase):
    def test_raycast_parameters_reasonable(self):
        """Test that raycast parameters work for typical player scenarios."""
        # Verify function accepts standard parameters
        entity = MockEntity(z=5.0)
        traverser = MagicMock()
        render = MockNodePath("render")
        
        # The function will return None without terrain, which is expected
        result = raycast_ground_height(entity, traverser, render)
        
        # In test environment with empty mocks, should return None gracefully
        self.assertIsNone(result)

    def test_raycast_ground_detection_integration(self):
        """Integration test for ground detection after jumping and falling."""
        entity = MockEntity(z=5.0)
        state = KinematicState(velocity_z=-10.0, grounded=False)
        
        # Simple ground check that returns ground at z=2.0
        def ground_check(e):
            # Simulate terrain at z=2.0
            if e.z <= 2.0:
                return 2.0
            return None
        
        # Integrate movement with ground check
        integrate_movement(entity, state, dt=1.0, ground_check=ground_check)
        
        # Entity should snap to ground
        self.assertEqual(entity.z, 2.0)
        self.assertEqual(state.velocity_z, 0.0)
        self.assertTrue(state.grounded)

    def test_ground_detection_while_jumping(self):
        """Test that player lands properly after a jump."""
        entity = MockEntity(z=2.0)  # Start on ground
        state = KinematicState(velocity_z=3.5, grounded=True)  # Jump velocity
        
        def ground_check(e):
            if e.z <= 2.0:
                return 2.0
            return None
        
        # Simulate several frames of a jump
        # Frame 1: Going up
        apply_gravity(state, dt=0.016, gravity=-12.0)
        integrate_movement(entity, state, dt=0.016, ground_check=ground_check)
        self.assertGreater(entity.z, 2.0)
        self.assertFalse(state.grounded)
        
        # Continue jumping until we start falling and land
        for _ in range(100):  # Enough frames to complete jump arc
            apply_gravity(state, dt=0.016, gravity=-12.0)
            integrate_movement(entity, state, dt=0.016, ground_check=ground_check)
            if state.grounded:
                break
        
        # Should land back on ground
        self.assertTrue(state.grounded)
        self.assertEqual(entity.z, 2.0)
        self.assertEqual(state.velocity_z, 0.0)

    def test_falling_from_significant_height(self):
        """Test that falling from high altitude works correctly."""
        entity = MockEntity(z=50.0)  # Start very high
        state = KinematicState(velocity_z=0.0, grounded=False)
        
        def ground_check(e):
            if e.z <= 2.0:
                return 2.0
            return None
        
        # Simulate falling
        max_iterations = 200  # Prevent infinite loop
        for i in range(max_iterations):
            apply_gravity(state, dt=0.016, gravity=-12.0, max_fall_speed=-30.0)
            integrate_movement(entity, state, dt=0.016, ground_check=ground_check)
            
            if state.grounded:
                break
        
        # Should land on ground even from high altitude
        self.assertTrue(state.grounded)
        self.assertEqual(entity.z, 2.0)
        self.assertLess(i, max_iterations - 1)
