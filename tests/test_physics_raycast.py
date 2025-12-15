"""Tests for raycast-based ground detection in physics system."""

from engine.physics import (
    KinematicState,
    apply_gravity,
    integrate_movement,
    raycast_ground_height,
)


class MockEntity:
    """Mock entity for testing without Ursina dependency."""
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.world_position = type('obj', (object,), {'x': x, 'y': y, 'z': z})()


def test_raycast_parameters_reasonable():
    """Test that raycast parameters work for typical player scenarios.
    
    This is a basic sanity test. Full raycast testing requires Ursina,
    so this just verifies the function signature and parameter defaults.
    """
    # Verify function accepts standard parameters
    entity = MockEntity(y=5.0)
    
    # The function will return None without Ursina available, which is expected
    result = raycast_ground_height(entity)
    
    # In test environment without Ursina, should return None gracefully
    assert result is None, "Should return None when Ursina is not available"


def test_raycast_ground_detection_integration():
    """Integration test for ground detection after jumping and falling.
    
    Tests the full physics integration with a simple ground check function.
    """
    entity = MockEntity(y=5.0)
    state = KinematicState(velocity_y=-10.0, grounded=False)
    
    # Simple ground check that returns ground at y=2.0
    def ground_check(e):
        # Simulate terrain at y=2.0
        if e.y <= 2.0:
            return 2.0
        return None
    
    # Integrate movement with ground check
    integrate_movement(entity, state, dt=1.0, ground_check=ground_check)
    
    # Entity should snap to ground
    assert entity.y == 2.0, f"Expected y=2.0, got {entity.y}"
    assert state.velocity_y == 0.0, "Vertical velocity should be zero on ground"
    assert state.grounded is True, "Should be marked as grounded"


def test_ground_detection_while_jumping():
    """Test that player lands properly after a jump."""
    entity = MockEntity(y=2.0)  # Start on ground
    state = KinematicState(velocity_y=3.5, grounded=True)  # Jump velocity
    
    def ground_check(e):
        if e.y <= 2.0:
            return 2.0
        return None
    
    # Simulate several frames of a jump
    # Frame 1: Going up
    apply_gravity(state, dt=0.016, gravity=-12.0)
    integrate_movement(entity, state, dt=0.016, ground_check=ground_check)
    assert entity.y > 2.0, "Should be airborne after jump"
    assert not state.grounded, "Should not be grounded while jumping"
    
    # Continue jumping until we start falling and land
    for _ in range(100):  # Enough frames to complete jump arc
        apply_gravity(state, dt=0.016, gravity=-12.0)
        integrate_movement(entity, state, dt=0.016, ground_check=ground_check)
        if state.grounded:
            break
    
    # Should land back on ground
    assert state.grounded, "Should land back on ground"
    assert entity.y == 2.0, "Should be at ground level"
    assert state.velocity_y == 0.0, "Velocity should be zero after landing"


def test_falling_from_significant_height():
    """Test that falling from high altitude works correctly."""
    entity = MockEntity(y=50.0)  # Start very high
    state = KinematicState(velocity_y=0.0, grounded=False)
    
    def ground_check(e):
        if e.y <= 2.0:
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
    assert state.grounded, "Should land on ground after falling"
    assert entity.y == 2.0, f"Should be at ground level, got {entity.y}"
    assert i < max_iterations - 1, "Should land within reasonable time"
