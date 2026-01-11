"""Unit tests for engine.core.math_utils."""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal, assert_almost_equal

from engine.core.math_utils import (
    normalize, normalize_batch, dot_batch, cross_batch,
    lerp, lerp_batch,
    euler_to_quat, quat_to_euler, quat_multiply, quat_slerp,
    rotation_matrix_x, rotation_matrix_y, rotation_matrix_z,
    smoothstep, smootherstep,
    ease_in_quad, ease_out_quad, ease_in_out_quad,
    distance, distance_squared, angle_between, project_onto_plane,
    clamp, remap
)


class TestVectorOperations:
    """Tests for vector operations."""
    
    def test_normalize_unit_vector(self):
        """Normalizing a unit vector should return itself."""
        v = np.array([1, 0, 0], dtype=np.float32)
        result = normalize(v)
        assert_array_almost_equal(result, v)
    
    def test_normalize_arbitrary_vector(self):
        """Normalizing should produce unit length."""
        v = np.array([3, 4, 0], dtype=np.float32)
        result = normalize(v)
        assert_almost_equal(np.linalg.norm(result), 1.0)
        assert_array_almost_equal(result, [0.6, 0.8, 0])
    
    def test_normalize_zero_vector(self):
        """Normalizing zero vector should return zero vector."""
        v = np.array([0, 0, 0], dtype=np.float32)
        result = normalize(v)
        assert_array_almost_equal(result, v)
    
    def test_normalize_batch(self):
        """Batch normalization should work on multiple vectors."""
        vectors = np.array([
            [3, 4, 0],
            [0, 0, 5],
            [1, 1, 1]
        ], dtype=np.float32)
        result = normalize_batch(vectors)
        
        # Check all have unit length
        lengths = np.linalg.norm(result, axis=1)
        assert_array_almost_equal(lengths, [1, 1, 1])
    
    def test_dot_batch(self):
        """Batch dot product calculation."""
        a = np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float32)
        b = np.array([[1, 0, 0], [0, 0, 1]], dtype=np.float32)
        result = dot_batch(a, b)
        assert_array_almost_equal(result, [1, 0])
    
    def test_cross_batch(self):
        """Batch cross product calculation."""
        a = np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float32)
        b = np.array([[0, 1, 0], [0, 0, 1]], dtype=np.float32)
        result = cross_batch(a, b)
        assert_array_almost_equal(result, [[0, 0, 1], [1, 0, 0]])


class TestInterpolation:
    """Tests for interpolation functions."""
    
    def test_lerp_scalar(self):
        """Linear interpolation of scalars."""
        assert lerp(0, 10, 0.5) == 5
        assert lerp(0, 10, 0) == 0
        assert lerp(0, 10, 1) == 10
    
    def test_lerp_vector(self):
        """Linear interpolation of vectors."""
        a = np.array([0, 0, 0], dtype=np.float32)
        b = np.array([10, 20, 30], dtype=np.float32)
        result = lerp(a, b, 0.5)
        assert_array_almost_equal(result, [5, 10, 15])
    
    def test_lerp_batch(self):
        """Batch linear interpolation."""
        a = np.array([[0, 0, 0], [10, 10, 10]], dtype=np.float32)
        b = np.array([[10, 10, 10], [20, 20, 20]], dtype=np.float32)
        t = np.array([0.5, 0.25], dtype=np.float32)
        result = lerp_batch(a, b, t)
        assert_array_almost_equal(result, [[5, 5, 5], [12.5, 12.5, 12.5]])


class TestQuaternions:
    """Tests for quaternion math."""
    
    def test_euler_to_quat_identity(self):
        """Zero rotation should give identity quaternion."""
        q = euler_to_quat(0, 0, 0)
        # Identity quaternion is [1, 0, 0, 0]
        assert_almost_equal(q[0], 1, decimal=5)  # w component
        assert_almost_equal(np.linalg.norm(q[1:]), 0, decimal=5)  # xyz near zero
    
    def test_euler_quat_single_axis(self):
        """Converting single-axis rotation should roundtrip correctly."""
        # Single-axis rotations don't have gimbal lock ambiguity
        for h, p, r in [(45, 0, 0), (0, 30, 0), (0, 0, 60)]:
            q = euler_to_quat(h, p, r)
            h2, p2, r2 = quat_to_euler(q)
            # At least one angle should match the input
            if h != 0:
                assert_almost_equal(h, h2, decimal=2)
            if p != 0:
                assert_almost_equal(p, p2, decimal=2)
            if r != 0:
                assert_almost_equal(r, r2, decimal=2)
    
    def test_quat_unit_length(self):
        """Quaternions from euler should have unit length."""
        q = euler_to_quat(30, 45, 60)
        assert_almost_equal(np.linalg.norm(q), 1.0)

    
    def test_quat_multiply_identity(self):
        """Multiplying by identity should not change quaternion."""
        identity = np.array([1, 0, 0, 0], dtype=np.float32)
        q = euler_to_quat(45, 30, 15)
        result = quat_multiply(q, identity)
        assert_array_almost_equal(result, q)
    
    def test_quat_slerp_endpoints(self):
        """Slerp at t=0 and t=1 should return start and end."""
        q1 = euler_to_quat(0, 0, 0)
        q2 = euler_to_quat(90, 0, 0)
        
        result_0 = quat_slerp(q1, q2, 0)
        result_1 = quat_slerp(q1, q2, 1)
        
        assert_array_almost_equal(result_0, q1)
        assert_array_almost_equal(result_1, q2)


class TestRotationMatrices:
    """Tests for rotation matrix generation."""
    
    def test_rotation_z_90(self):
        """90 degree Z rotation should swap X and Y."""
        mat = rotation_matrix_z(90)
        v = np.array([1, 0, 0], dtype=np.float32)
        result = mat @ v
        assert_array_almost_equal(result, [0, 1, 0])
    
    def test_rotation_x_90(self):
        """90 degree X rotation should swap Y and Z."""
        mat = rotation_matrix_x(90)
        v = np.array([0, 1, 0], dtype=np.float32)
        result = mat @ v
        assert_array_almost_equal(result, [0, 0, 1])
    
    def test_rotation_y_90(self):
        """90 degree Y rotation should swap X and Z."""
        mat = rotation_matrix_y(90)
        v = np.array([0, 0, 1], dtype=np.float32)
        result = mat @ v
        assert_array_almost_equal(result, [1, 0, 0])


class TestEasing:
    """Tests for easing functions."""
    
    def test_smoothstep_boundaries(self):
        """Smoothstep should be 0 at t=0 and 1 at t=1."""
        assert smoothstep(0) == 0
        assert smoothstep(1) == 1
    
    def test_smoothstep_midpoint(self):
        """Smoothstep at t=0.5 should be 0.5."""
        assert smoothstep(0.5) == 0.5
    
    def test_smootherstep_boundaries(self):
        """Smootherstep should be 0 at t=0 and 1 at t=1."""
        assert smootherstep(0) == 0
        assert smootherstep(1) == 1
    
    def test_ease_in_quad(self):
        """Quadratic ease-in should be slow at start."""
        assert ease_in_quad(0) == 0
        assert ease_in_quad(0.5) == 0.25
        assert ease_in_quad(1) == 1
    
    def test_ease_out_quad(self):
        """Quadratic ease-out should be fast at start."""
        assert ease_out_quad(0) == 0
        assert ease_out_quad(0.5) == 0.75
        assert ease_out_quad(1) == 1


class TestGeometry:
    """Tests for geometric utilities."""
    
    def test_distance(self):
        """Euclidean distance calculation."""
        a = np.array([0, 0, 0], dtype=np.float32)
        b = np.array([3, 4, 0], dtype=np.float32)
        assert distance(a, b) == 5
    
    def test_distance_squared(self):
        """Squared distance for comparisons."""
        a = np.array([0, 0, 0], dtype=np.float32)
        b = np.array([3, 4, 0], dtype=np.float32)
        assert distance_squared(a, b) == 25
    
    def test_angle_between_perpendicular(self):
        """Perpendicular vectors should have 90 degree angle."""
        a = np.array([1, 0, 0], dtype=np.float32)
        b = np.array([0, 1, 0], dtype=np.float32)
        assert_almost_equal(angle_between(a, b), 90)
    
    def test_angle_between_parallel(self):
        """Parallel vectors should have 0 degree angle."""
        a = np.array([1, 0, 0], dtype=np.float32)
        b = np.array([2, 0, 0], dtype=np.float32)
        assert_almost_equal(angle_between(a, b), 0)
    
    def test_project_onto_plane(self):
        """Vector projection onto XY plane."""
        v = np.array([1, 1, 1], dtype=np.float32)
        normal = np.array([0, 0, 1], dtype=np.float32)
        result = project_onto_plane(v, normal)
        assert_array_almost_equal(result, [1, 1, 0])
    
    def test_clamp(self):
        """Value clamping."""
        assert clamp(5, 0, 10) == 5
        assert clamp(-5, 0, 10) == 0
        assert clamp(15, 0, 10) == 10
    
    def test_remap(self):
        """Value remapping between ranges."""
        assert remap(5, 0, 10, 0, 100) == 50
        assert remap(0, 0, 10, 100, 200) == 100
        assert remap(10, 0, 10, 100, 200) == 200
