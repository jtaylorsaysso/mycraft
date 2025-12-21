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
    normal = (0, 1, 0)  # Pointing straight up
    angle = calculate_slope_angle(normal)
    assert abs(angle - 0.0) < 0.01


def test_slope_angle_45_degrees():
    """45° slope should be detected correctly."""
    # Normal at 45° from vertical (Y-up)
    # n_y = cos(45) = 0.707
    normal = (0.707, 0.707, 0)
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
    normal = (0, 1, 0)
    projected = project_velocity_onto_slope(vel, normal)
    assert abs(projected[0] - 5.0) < 0.01
    assert abs(projected[1] - 0.0) < 0.01
    assert abs(projected[2] - 0.0) < 0.01


def test_velocity_projection_slope():
    """Velocity on slope should have vertical component."""
    vel = (5.0, 0.0, 0.0)
    normal = (0.707, 0.707, 0)  # 45° slope in X direction
    projected = project_velocity_onto_slope(vel, normal)
    
    # Should have both X and Y components (in physics Y is up)
    # v_projected = v - (v·n)n = (5,0,0) - (5*0.707)*(0.707, 0.707, 0)
    # = (5,0,0) - (2.5, 2.5, 0) = (2.5, -2.5, 0)
    # Wait, my project_velocity_onto_slope:
    # dot = vx*nx + vy*ny + vz*nz = 5*0.707 = 3.535
    # vx_proj = 5 - 3.535*0.707 = 5 - 2.5 = 2.5
    # vy_proj = 0 - 3.535*0.707 = -2.5
    assert abs(projected[0] - 2.5) < 0.1
    assert abs(projected[1] - (-2.5)) < 0.1


def test_downslope_direction_flat():
    """Flat surface has no downslope direction."""
    normal = (0, 1, 0)
    downslope = get_downslope_direction(normal)
    assert abs(downslope[0]) < 0.01
    assert abs(downslope[2]) < 0.01


def test_downslope_direction_slope():
    """Slope should have clear downslope direction."""
    # Slope tilted in +X direction (normal points back in -X)
    # Wait, if it tilts up towards +X, normal points in -X direction
    # our downslope is negated horizontal component of normal
    # normal = (-0.5, 0.866, 0) -> downslope = (+0.5, 0) normalized -> (1, 0)
    normal = (-0.5, 0.866, 0)  # ~30° slope rising in +X
    downslope = get_downslope_direction(normal)
    
    # Downslope should point in +Z/X away from normal
    assert downslope[0] > 0.9  # Mostly in X
    assert abs(downslope[1]) < 0.01  # No Y component in downslope dir vector
    assert abs(downslope[2]) < 0.01  # No Z component


def test_sliding_state_steep_slope():
    """Slopes steeper than MAX_WALKABLE_SLOPE should trigger sliding."""
    state = KinematicState()
    normal = (0.866, 0.5, 0)  # normal.y = 0.5 -> cos(angle) = 0.5 -> angle = 60°
    state.surface_normal = normal
    state.slope_angle = calculate_slope_angle(normal)
    state.grounded = True
    
    assert state.slope_angle > MAX_WALKABLE_SLOPE


def test_sliding_applies_downslope_force():
    """Sliding should add velocity in downslope direction."""
    state = KinematicState()
    state.sliding = True
    state.surface_normal = (-0.707, 0.707, 0)  # 45° slope rising in +X (normal points -X)
    state.velocity_x = 0.0
    state.velocity_z = 0.0
    
    apply_slope_forces(state, dt=0.1)
    
    # Downslope should be +X
    assert state.velocity_x > 0.0


def test_slope_jump_boost_uphill():
    """Jumping while moving uphill should add vertical velocity."""
    state = KinematicState()
    state.grounded = True
    # Normal points +X, so rising in +X
    state.surface_normal = (0.5, 0.866, 0)  # ~30° slope rising in +X
    state.slope_angle = 30.0
    state.velocity_x = 5.0  # Moving uphill (+X)
    state.velocity_z = 0.0
    
    slope_vel = get_slope_velocity_component(state)
    
    # Should have positive vertical component (boost upward)
    assert slope_vel[1] > 0.0


def test_slope_jump_boost_downhill():
    """Jumping while moving downhill should reduce vertical velocity."""
    state = KinematicState()
    state.grounded = True
    # Normal points +X, so rising in +X
    state.surface_normal = (0.5, 0.866, 0)  # ~30° slope rising in +X
    state.slope_angle = 30.0
    state.velocity_x = -5.0  # Moving downhill (-X)
    state.velocity_z = 0.0
    
    slope_vel = get_slope_velocity_component(state)
    
    # Should have negative vertical component (less upward boost)
    assert slope_vel[1] < 0.0
