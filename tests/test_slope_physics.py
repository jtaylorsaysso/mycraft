"""Tests for slope physics: angle calculation, sliding, and velocity projection."""

import math
import pytest
from engine.physics.kinematic import (
    KinematicState,
    calculate_slope_angle,
    project_velocity_onto_slope,
    get_downslope_direction,
    get_slope_velocity_component,
    apply_slope_forces
)
from engine.physics.constants import MAX_WALKABLE_SLOPE


def test_slope_angle_flat():
    """Flat surface should have 0° angle."""
    normal = (0, 0, 1)  # Pointing straight up (Z-up in Panda3D)
    angle = calculate_slope_angle(normal)
    assert abs(angle - 0.0) < 0.01


def test_slope_angle_45_degrees():
    """45° slope should be detected correctly."""
    # Normal at 45° from vertical (Z-up in Panda3D)
    # n_z = cos(45) = 0.707
    normal = (0.707, 0, 0.707)
    angle = calculate_slope_angle(normal)
    assert abs(angle - 45.0) < 1.0


def test_slope_angle_vertical():
    """Vertical wall should be 90°."""
    normal = (1, 0, 0)  # Horizontal normal = vertical surface
    angle = calculate_slope_angle(normal)
    assert abs(angle - 90.0) < 0.01


def test_velocity_projection_flat():
    """Velocity on flat ground should be unchanged."""
    vel = (5.0, 0.0, 0.0)
    normal = (0, 0, 1)  # Z-up
    projected = project_velocity_onto_slope(vel, normal)
    assert abs(projected[0] - 5.0) < 0.01
    assert abs(projected[1] - 0.0) < 0.01
    assert abs(projected[2] - 0.0) < 0.01


def test_velocity_projection_slope():
    """Velocity on slope should have vertical component."""
    vel = (5.0, 0.0, 0.0)
    normal = (0.707, 0, 0.707)  # 45° slope in X direction (Z-up)
    projected = project_velocity_onto_slope(vel, normal)
    
    # Should have both X and Z components (in Panda3D Z is up)
    assert abs(projected[0] - 2.5) < 0.1
    assert abs(projected[2] - (-2.5)) < 0.1


def test_downslope_direction_flat():
    """Flat surface has no downslope direction."""
    normal = (0, 0, 1)  # Z-up
    downslope = get_downslope_direction(normal)
    assert abs(downslope[0]) < 0.01
    assert abs(downslope[1]) < 0.01


def test_downslope_direction_slope():
    """Slope should have clear downslope direction."""
    # Slope tilted in +X direction (normal points back in -X, up in +Z)
    normal = (-0.5, 0, 0.866)  # ~30° slope rising in +X
    downslope = get_downslope_direction(normal)
    
    # Downslope should point in +X (horizontal component of -normal)
    assert downslope[0] > 0.9  # Mostly in X
    assert abs(downslope[1]) < 0.01  # No Y component
    assert abs(downslope[2]) < 0.01  # No Z component (downslope is horizontal)


def test_sliding_state_steep_slope():
    """Slopes steeper than MAX_WALKABLE_SLOPE should trigger sliding."""
    state = KinematicState()
    normal = (0.866, 0, 0.5)  # normal.z = 0.5 -> cos(angle) = 0.5 -> angle = 60°
    state.surface_normal = normal
    state.slope_angle = calculate_slope_angle(normal)
    state.grounded = True
    
    assert state.slope_angle > MAX_WALKABLE_SLOPE


def test_sliding_applies_downslope_force():
    """Sliding should add velocity in downslope direction."""
    state = KinematicState()
    state.sliding = True
    state.surface_normal = (-0.707, 0, 0.707)  # 45° slope rising in +X (normal points -X, +Z)
    state.velocity_x = 0.0
    state.velocity_y = 0.0
    
    apply_slope_forces(state, dt=0.1)
    
    # Downslope should be +X
    assert state.velocity_x > 0.0


def test_slope_jump_boost_uphill():
    """Jumping while moving uphill should add vertical velocity."""
    state = KinematicState()
    state.grounded = True
    # Normal points +X and +Z, so rising in +X
    state.surface_normal = (0.5, 0, 0.866)  # ~30° slope rising in +X
    state.slope_angle = 30.0
    state.velocity_x = 5.0  # Moving uphill (+X)
    state.velocity_y = 0.0
    
    slope_vel = get_slope_velocity_component(state)
    
    # Should have positive vertical component (boost upward) - index 2 is Z
    assert slope_vel[2] > 0.0


def test_slope_jump_boost_downhill():
    """Jumping while moving downhill should reduce vertical velocity."""
    state = KinematicState()
    state.grounded = True
    # Normal points +X and +Z, so rising in +X
    state.surface_normal = (0.5, 0, 0.866)  # ~30° slope rising in +X
    state.slope_angle = 30.0
    state.velocity_x = -5.0  # Moving downhill (-X)
    state.velocity_y = 0.0
    
    slope_vel = get_slope_velocity_component(state)
    
    # Should have negative vertical component (less upward boost) - index 2 is Z
    assert slope_vel[2] < 0.0
