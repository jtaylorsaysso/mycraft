"""
SpineSpline: Catmull-Rom spline for spine curve manipulation.

Provides smooth interpolation through control points for organic spine bending.
"""

from typing import List
from panda3d.core import LVector3f


class SpineSpline:
    """Catmull-Rom spline for smooth spine curves.
    
    Properties:
    - Passes through all control points
    - C1 continuous (smooth tangents)
    - Local control (moving one point affects nearby segments)
    """
    
    def __init__(self, control_points: List[LVector3f]):
        """Initialize spline with control points.
        
        Args:
            control_points: At least 4 points [hips, lower, upper, chest]
        """
        if len(control_points) < 4:
            raise ValueError("Catmull-Rom spline requires at least 4 control points")
        
        self.control_points = [LVector3f(p) for p in control_points]
        
    def evaluate(self, t: float) -> LVector3f:
        """Evaluate position on the spline at parameter t.
        
        Args:
            t: Parameter in [0, 1], where 0 = first point, 1 = last point
            
        Returns:
            Position on the curve
        """
        t = max(0.0, min(1.0, t))  # Clamp to [0, 1]
        
        # Map t to segment index
        n_segments = len(self.control_points) - 3
        segment_t = t * n_segments
        segment_idx = int(segment_t)
        
        # Handle edge case: t = 1.0
        if segment_idx >= n_segments:
            segment_idx = n_segments - 1
            segment_t = float(n_segments)
        
        # Local parameter within segment [0, 1]
        local_t = segment_t - segment_idx
        
        # Get 4 control points for this segment
        p0 = self.control_points[segment_idx]
        p1 = self.control_points[segment_idx + 1]
        p2 = self.control_points[segment_idx + 2]
        p3 = self.control_points[segment_idx + 3]
        
        return self._catmull_rom(p0, p1, p2, p3, local_t)
    
    def tangent(self, t: float) -> LVector3f:
        """Evaluate tangent (direction) on the spline at parameter t.
        
        Args:
            t: Parameter in [0, 1]
            
        Returns:
            Normalized direction vector
        """
        t = max(0.0, min(1.0, t))
        
        # Map t to segment
        n_segments = len(self.control_points) - 3
        segment_t = t * n_segments
        segment_idx = int(segment_t)
        
        if segment_idx >= n_segments:
            segment_idx = n_segments - 1
            segment_t = float(n_segments)
        
        local_t = segment_t - segment_idx
        
        # Get 4 control points
        p0 = self.control_points[segment_idx]
        p1 = self.control_points[segment_idx + 1]
        p2 = self.control_points[segment_idx + 2]
        p3 = self.control_points[segment_idx + 3]
        
        tangent_vec = self._catmull_rom_derivative(p0, p1, p2, p3, local_t)
        
        # Normalize
        length = tangent_vec.length()
        if length > 0.0001:
            tangent_vec /= length
            
        return tangent_vec
    
    def set_control_point(self, index: int, position: LVector3f):
        """Update a control point position.
        
        Args:
            index: Control point index
            position: New position
        """
        if 0 <= index < len(self.control_points):
            self.control_points[index] = LVector3f(position)
        else:
            raise IndexError(f"Control point index {index} out of range")
    
    def get_control_points(self) -> List[LVector3f]:
        """Get all control points.
        
        Returns:
            Copy of control points list
        """
        return [LVector3f(p) for p in self.control_points]
    
    def _catmull_rom(self, p0: LVector3f, p1: LVector3f, 
                     p2: LVector3f, p3: LVector3f, t: float) -> LVector3f:
        """Catmull-Rom interpolation between p1 and p2.
        
        Uses p0 and p3 to determine tangents.
        
        Formula (component-wise):
        P(t) = 0.5 * [
            (-p0 + 3*p1 - 3*p2 + p3) * t^3 +
            (2*p0 - 5*p1 + 4*p2 - p3) * t^2 +
            (-p0 + p2) * t +
            2*p1
        ]
        
        Args:
            p0, p1, p2, p3: Four consecutive control points
            t: Parameter in [0, 1]
            
        Returns:
            Interpolated position
        """
        t2 = t * t
        t3 = t2 * t
        
        # Compute x, y, z components separately
        x = 0.0
        y = 0.0
        z = 0.0
        
        # X component
        c0 = -p0.x + 3*p1.x - 3*p2.x + p3.x
        c1 = 2*p0.x - 5*p1.x + 4*p2.x - p3.x
        c2 = -p0.x + p2.x
        c3 = 2*p1.x
        x = 0.5 * (c0 * t3 + c1 * t2 + c2 * t + c3)
        
        # Y component
        c0 = -p0.y + 3*p1.y - 3*p2.y + p3.y
        c1 = 2*p0.y - 5*p1.y + 4*p2.y - p3.y
        c2 = -p0.y + p2.y
        c3 = 2*p1.y
        y = 0.5 * (c0 * t3 + c1 * t2 + c2 * t + c3)
        
        # Z component
        c0 = -p0.z + 3*p1.z - 3*p2.z + p3.z
        c1 = 2*p0.z - 5*p1.z + 4*p2.z - p3.z
        c2 = -p0.z + p2.z
        c3 = 2*p1.z
        z = 0.5 * (c0 * t3 + c1 * t2 + c2 * t + c3)
        
        return LVector3f(x, y, z)
    
    def _catmull_rom_derivative(self, p0: LVector3f, p1: LVector3f,
                                 p2: LVector3f, p3: LVector3f, t: float) -> LVector3f:
        """Derivative of Catmull-Rom curve (tangent vector).
        
        Formula (component-wise):
        P'(t) = 0.5 * [
            3*(-p0 + 3*p1 - 3*p2 + p3) * t^2 +
            2*(2*p0 - 5*p1 + 4*p2 - p3) * t +
            (-p0 + p2)
        ]
        
        Args:
            p0, p1, p2, p3: Four consecutive control points
            t: Parameter in [0, 1]
            
        Returns:
            Tangent vector (not normalized)
        """
        t2 = t * t
        
        # Compute x, y, z components separately
        x = 0.0
        y = 0.0
        z = 0.0
        
        # X component
        c0 = -p0.x + 3*p1.x - 3*p2.x + p3.x
        c1 = 2*p0.x - 5*p1.x + 4*p2.x - p3.x
        c2 = -p0.x + p2.x
        x = 0.5 * (3 * c0 * t2 + 2 * c1 * t + c2)
        
        # Y component
        c0 = -p0.y + 3*p1.y - 3*p2.y + p3.y
        c1 = 2*p0.y - 5*p1.y + 4*p2.y - p3.y
        c2 = -p0.y + p2.y
        y = 0.5 * (3 * c0 * t2 + 2 * c1 * t + c2)
        
        # Z component
        c0 = -p0.z + 3*p1.z - 3*p2.z + p3.z
        c1 = 2*p0.z - 5*p1.z + 4*p2.z - p3.z
        c2 = -p0.z + p2.z
        z = 0.5 * (3 * c0 * t2 + 2 * c1 * t + c2)
        
        return LVector3f(x, y, z)
    
    def sample_points(self, num_samples: int = 20) -> List[LVector3f]:
        """Sample points along the curve for visualization.
        
        Args:
            num_samples: Number of points to sample
            
        Returns:
            List of positions along the curve
        """
        if num_samples < 2:
            num_samples = 2
            
        samples = []
        for i in range(num_samples):
            t = i / (num_samples - 1)
            samples.append(self.evaluate(t))
            
        return samples
