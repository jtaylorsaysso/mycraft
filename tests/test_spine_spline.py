"""
Unit tests for SpineSpline.
"""

import pytest
from panda3d.core import LVector3f
from engine.editor.tools.common.spine_spline import SpineSpline


class TestSpineSpline:
    """Test Catmull-Rom spline interpolation."""
    
    def test_initialization(self):
        """Test spline creation with control points."""
        points = [
            LVector3f(0, 0, 0),
            LVector3f(0, 0, 1),
            LVector3f(0, 0, 2),
            LVector3f(0, 0, 3),
        ]
        spline = SpineSpline(points)
        
        assert len(spline.control_points) == 4
        # Check components instead of equality
        assert abs(spline.control_points[0].x - 0) < 0.0001
        assert abs(spline.control_points[0].z - 0) < 0.0001
        assert abs(spline.control_points[3].z - 3) < 0.0001
    
    def test_requires_minimum_points(self):
        """Test that spline requires at least 4 points."""
        with pytest.raises(ValueError):
            SpineSpline([LVector3f(0, 0, 0)])
        
        with pytest.raises(ValueError):
            SpineSpline([LVector3f(0, 0, 0), LVector3f(1, 1, 1)])
    
    def test_passes_through_interior_points(self):
        """Test that curve passes through p1 and p2."""
        points = [
            LVector3f(0, 0, 0),
            LVector3f(0, 0, 1),  # Should pass through this at t=0
            LVector3f(0, 0, 2),  # Should pass through this at t=1
            LVector3f(0, 0, 3),
        ]
        spline = SpineSpline(points)
        
        # At t=0, should be at p1
        p_start = spline.evaluate(0.0)
        assert abs(p_start.z - 1.0) < 0.0001
        
        # At t=1, should be at p2 (last interior point)
        p_end = spline.evaluate(1.0)
        assert abs(p_end.z - 2.0) < 0.0001
    
    def test_smooth_interpolation(self):
        """Test that curve is smooth between points."""
        points = [
            LVector3f(0, 0, 0),
            LVector3f(0, 0, 1),
            LVector3f(0, 0, 2),
            LVector3f(0, 0, 3),
        ]
        spline = SpineSpline(points)
        
        # Sample at midpoint
        p_mid = spline.evaluate(0.5)
        
        # Should be between p1 and p2 on Z
        assert 1.0 < p_mid.z < 2.0
    
    def test_tangent_direction(self):
        """Test that tangent points in forward direction."""
        points = [
            LVector3f(0, 0, 0),
            LVector3f(0, 0, 1),
            LVector3f(0, 0, 2),
            LVector3f(0, 0, 3),
        ]
        spline = SpineSpline(points)
        
        # Tangent at t=0.5
        tangent = spline.tangent(0.5)
        
        # Should be normalized
        length = tangent.length()
        assert abs(length - 1.0) < 0.0001
        
        # Should point generally upward (positive Z)
        assert tangent.z > 0
    
    def test_set_control_point(self):
        """Test updating control points."""
        points = [
            LVector3f(0, 0, 0),
            LVector3f(0, 0, 1),
            LVector3f(0, 0, 2),
            LVector3f(0, 0, 3),
        ]
        spline = SpineSpline(points)
        
        # Move second point
        new_pos = LVector3f(1, 0, 1)
        spline.set_control_point(1, new_pos)
        
        # Check components
        assert abs(spline.control_points[1].x - 1.0) < 0.0001
        assert abs(spline.control_points[1].z - 1.0) < 0.0001
        
        # Curve should now pass through new position at t=0
        p = spline.evaluate(0.0)
        assert abs(p.x - 1.0) < 0.0001
    
    def test_set_control_point_out_of_range(self):
        """Test invalid control point index."""
        points = [
            LVector3f(0, 0, 0),
            LVector3f(0, 0, 1),
            LVector3f(0, 0, 2),
            LVector3f(0, 0, 3),
        ]
        spline = SpineSpline(points)
        
        with pytest.raises(IndexError):
            spline.set_control_point(10, LVector3f(0, 0, 0))
    
    def test_get_control_points(self):
        """Test getting control points returns a copy."""
        points = [
            LVector3f(0, 0, 0),
            LVector3f(0, 0, 1),
            LVector3f(0, 0, 2),
            LVector3f(0, 0, 3),
        ]
        spline = SpineSpline(points)
        
        retrieved = spline.get_control_points()
        
        # Should be a copy
        assert retrieved is not spline.control_points
        assert len(retrieved) == 4
        # Check components
        assert abs(retrieved[0].x - points[0].x) < 0.0001
        assert abs(retrieved[0].z - points[0].z) < 0.0001
    
    def test_sample_points(self):
        """Test curve sampling for visualization."""
        points = [
            LVector3f(0, 0, 0),
            LVector3f(0, 0, 1),
            LVector3f(0, 0, 2),
            LVector3f(0, 0, 3),
        ]
        spline = SpineSpline(points)
        
        samples = spline.sample_points(10)
        
        assert len(samples) == 10
        # First sample should be near p1
        assert abs(samples[0].z - 1.0) < 0.0001
        # Last sample should be near p2
        assert abs(samples[-1].z - 2.0) < 0.0001
    
    def test_curved_spine(self):
        """Test a curved (non-straight) spine."""
        points = [
            LVector3f(0, -1, 0),   # Behind
            LVector3f(0, 0, 1),    # Hips
            LVector3f(0, 1, 2),    # Chest (forward)
            LVector3f(0, 1, 3),    # Head
        ]
        spline = SpineSpline(points)
        
        # At t=0.5, should have moved forward in Y
        p_mid = spline.evaluate(0.5)
        assert p_mid.y > 0  # Should be forward of hips
