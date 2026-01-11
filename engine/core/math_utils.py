"""NumPy-based mathematical utilities for the engine.

Provides optimized vector, rotation, and interpolation operations using NumPy.
Includes utilities for converting between Panda3D types and NumPy arrays.
"""

import numpy as np
from typing import Union, Tuple, Optional
from numpy.typing import NDArray

# Type aliases for clarity
Vec3 = NDArray[np.float32]  # Shape (3,)
Vec3Array = NDArray[np.float32]  # Shape (N, 3)
Mat3 = NDArray[np.float32]  # Shape (3, 3)
Mat4 = NDArray[np.float32]  # Shape (4, 4)
Quat = NDArray[np.float32]  # Shape (4,) - [w, x, y, z]


# =============================================================================
# Vector Operations
# =============================================================================

def normalize(v: Vec3) -> Vec3:
    """Normalize a vector to unit length.
    
    Args:
        v: Input vector (3,)
        
    Returns:
        Normalized vector, or zero vector if input is zero
    """
    length = np.linalg.norm(v)
    if length < 1e-10:
        return np.zeros(3, dtype=np.float32)
    return v / length


def normalize_batch(vectors: Vec3Array) -> Vec3Array:
    """Normalize an array of vectors.
    
    Args:
        vectors: Input vectors (N, 3)
        
    Returns:
        Normalized vectors (N, 3)
    """
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    # Avoid division by zero
    lengths = np.where(lengths < 1e-10, 1.0, lengths)
    return vectors / lengths


def dot_batch(a: Vec3Array, b: Vec3Array) -> NDArray[np.float32]:
    """Compute dot products for arrays of vectors.
    
    Args:
        a: First vectors (N, 3)
        b: Second vectors (N, 3)
        
    Returns:
        Dot products (N,)
    """
    return np.sum(a * b, axis=1)


def cross_batch(a: Vec3Array, b: Vec3Array) -> Vec3Array:
    """Compute cross products for arrays of vectors.
    
    Args:
        a: First vectors (N, 3)
        b: Second vectors (N, 3)
        
    Returns:
        Cross products (N, 3)
    """
    return np.cross(a, b)


def lerp(a: Union[float, Vec3], b: Union[float, Vec3], t: float) -> Union[float, Vec3]:
    """Linear interpolation between two values.
    
    Args:
        a: Start value (scalar or vector)
        b: End value (scalar or vector)
        t: Interpolation factor (0-1)
        
    Returns:
        Interpolated value
    """
    return a + (b - a) * t


def lerp_batch(a: Vec3Array, b: Vec3Array, t: NDArray[np.float32]) -> Vec3Array:
    """Linear interpolation for arrays of vectors.
    
    Args:
        a: Start vectors (N, 3)
        b: End vectors (N, 3)
        t: Interpolation factors (N,) or (N, 1)
        
    Returns:
        Interpolated vectors (N, 3)
    """
    if t.ndim == 1:
        t = t[:, np.newaxis]
    return a + (b - a) * t


# =============================================================================
# Rotation Operations
# =============================================================================

def euler_to_quat(h: float, p: float, r: float) -> Quat:
    """Convert Euler angles (HPR) to quaternion.
    
    Uses Panda3D's HPR convention (ZXY extrinsic = YXZ intrinsic):
    - H (heading/yaw): rotation around Z axis
    - P (pitch): rotation around X axis  
    - R (roll): rotation around Y axis
    
    Args:
        h: Heading in degrees
        p: Pitch in degrees
        r: Roll in degrees
        
    Returns:
        Quaternion [w, x, y, z]
    """
    # Convert to radians and half-angles
    h_rad = np.radians(h) / 2  # Z axis (heading)
    p_rad = np.radians(p) / 2  # X axis (pitch)
    r_rad = np.radians(r) / 2  # Y axis (roll)
    
    # Create individual axis quaternions
    # Q_h (heading around Z): [cos(h/2), 0, 0, sin(h/2)]
    # Q_p (pitch around X): [cos(p/2), sin(p/2), 0, 0]
    # Q_r (roll around Y): [cos(r/2), 0, sin(r/2), 0]
    
    ch, sh = np.cos(h_rad), np.sin(h_rad)
    cp, sp = np.cos(p_rad), np.sin(p_rad)
    cr, sr = np.cos(r_rad), np.sin(r_rad)
    
    # Combined rotation: Rh * Rp * Rr (HPR order, applied right to left)
    w = ch * cp * cr - sh * sp * sr
    x = ch * sp * cr + sh * cp * sr
    y = ch * cp * sr + sh * sp * cr
    z = sh * cp * cr - ch * sp * sr
    
    return np.array([w, x, y, z], dtype=np.float32)


def quat_to_euler(q: Quat) -> Tuple[float, float, float]:
    """Convert quaternion to Euler angles (HPR).
    
    Args:
        q: Quaternion [w, x, y, z]
        
    Returns:
        (heading, pitch, roll) in degrees
    """
    w, x, y, z = q
    
    # Heading (Z axis rotation)
    sin_h = 2 * (w * z + x * y)
    cos_h = 1 - 2 * (y * y + z * z)
    h = np.degrees(np.arctan2(sin_h, cos_h))
    
    # Pitch (X axis rotation) - use asin with clamping for gimbal lock
    sin_p = 2 * (w * x - z * y)
    sin_p = np.clip(sin_p, -1, 1)
    p = np.degrees(np.arcsin(sin_p))
    
    # Roll (Y axis rotation)
    sin_r = 2 * (w * y + x * z)
    cos_r = 1 - 2 * (x * x + y * y)
    r = np.degrees(np.arctan2(sin_r, cos_r))
    
    return (h, p, r)


def quat_multiply(q1: Quat, q2: Quat) -> Quat:
    """Multiply two quaternions (compose rotations).
    
    Args:
        q1: First quaternion [w, x, y, z]
        q2: Second quaternion [w, x, y, z]
        
    Returns:
        Product quaternion (q1 * q2)
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    
    return np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ], dtype=np.float32)


def quat_slerp(q1: Quat, q2: Quat, t: float) -> Quat:
    """Spherical linear interpolation between quaternions.
    
    Args:
        q1: Start quaternion
        q2: End quaternion
        t: Interpolation factor (0-1)
        
    Returns:
        Interpolated quaternion
    """
    # Ensure shortest path
    dot = np.dot(q1, q2)
    if dot < 0:
        q2 = -q2
        dot = -dot
    
    # Linear interpolation for very close quaternions
    if dot > 0.9995:
        result = lerp(q1, q2, t)
        return result / np.linalg.norm(result)
    
    theta_0 = np.arccos(dot)
    theta = theta_0 * t
    
    sin_theta = np.sin(theta)
    sin_theta_0 = np.sin(theta_0)
    
    s1 = np.cos(theta) - dot * sin_theta / sin_theta_0
    s2 = sin_theta / sin_theta_0
    
    return s1 * q1 + s2 * q2


def rotation_matrix_z(angle_deg: float) -> Mat3:
    """Create rotation matrix around Z axis.
    
    Args:
        angle_deg: Rotation angle in degrees
        
    Returns:
        3x3 rotation matrix
    """
    rad = np.radians(angle_deg)
    c, s = np.cos(rad), np.sin(rad)
    return np.array([
        [c, -s, 0],
        [s, c, 0],
        [0, 0, 1]
    ], dtype=np.float32)


def rotation_matrix_x(angle_deg: float) -> Mat3:
    """Create rotation matrix around X axis."""
    rad = np.radians(angle_deg)
    c, s = np.cos(rad), np.sin(rad)
    return np.array([
        [1, 0, 0],
        [0, c, -s],
        [0, s, c]
    ], dtype=np.float32)


def rotation_matrix_y(angle_deg: float) -> Mat3:
    """Create rotation matrix around Y axis."""
    rad = np.radians(angle_deg)
    c, s = np.cos(rad), np.sin(rad)
    return np.array([
        [c, 0, s],
        [0, 1, 0],
        [-s, 0, c]
    ], dtype=np.float32)


# =============================================================================
# Easing Functions
# =============================================================================

def ease_in_quad(t: float) -> float:
    """Quadratic ease-in."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out."""
    return 1 - (1 - t) ** 2


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out."""
    if t < 0.5:
        return 2 * t * t
    return 1 - ((-2 * t + 2) ** 2) / 2


def ease_in_cubic(t: float) -> float:
    """Cubic ease-in."""
    return t * t * t


def ease_out_cubic(t: float) -> float:
    """Cubic ease-out."""
    return 1 - (1 - t) ** 3


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - ((-2 * t + 2) ** 3) / 2


def smoothstep(t: float) -> float:
    """Hermite smoothstep (same as CSS ease-in-out)."""
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def smootherstep(t: float) -> float:
    """Ken Perlin's improved smoothstep (6t^5 - 15t^4 + 10t^3)."""
    t = np.clip(t, 0, 1)
    return t * t * t * (t * (t * 6 - 15) + 10)


# =============================================================================
# Panda3D Conversions
# =============================================================================

def vec3_to_numpy(v) -> Vec3:
    """Convert Panda3D LVector3f to NumPy array.
    
    Args:
        v: Panda3D LVector3f or similar
        
    Returns:
        NumPy array (3,)
    """
    return np.array([v.x, v.y, v.z], dtype=np.float32)


def numpy_to_vec3(arr: Vec3):
    """Convert NumPy array to Panda3D LVector3f.
    
    Args:
        arr: NumPy array (3,)
        
    Returns:
        Panda3D LVector3f
    """
    from panda3d.core import LVector3f
    return LVector3f(float(arr[0]), float(arr[1]), float(arr[2]))


def quat_to_numpy(q) -> Quat:
    """Convert Panda3D LQuaternionf to NumPy array.
    
    Args:
        q: Panda3D LQuaternionf
        
    Returns:
        NumPy array [w, x, y, z]
    """
    return np.array([q.getW(), q.getX(), q.getY(), q.getZ()], dtype=np.float32)


def numpy_to_quat(arr: Quat):
    """Convert NumPy array to Panda3D LQuaternionf.
    
    Args:
        arr: NumPy array [w, x, y, z]
        
    Returns:
        Panda3D LQuaternionf
    """
    from panda3d.core import LQuaternionf
    return LQuaternionf(float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3]))


# =============================================================================
# Geometric Utilities
# =============================================================================

def distance(a: Vec3, b: Vec3) -> float:
    """Euclidean distance between two points."""
    return np.linalg.norm(b - a)


def distance_squared(a: Vec3, b: Vec3) -> float:
    """Squared Euclidean distance (avoid sqrt for comparisons)."""
    diff = b - a
    return np.dot(diff, diff)


def angle_between(a: Vec3, b: Vec3) -> float:
    """Angle between two vectors in degrees."""
    a_norm = normalize(a)
    b_norm = normalize(b)
    dot = np.clip(np.dot(a_norm, b_norm), -1, 1)
    return np.degrees(np.arccos(dot))


def project_onto_plane(v: Vec3, normal: Vec3) -> Vec3:
    """Project vector onto plane defined by normal.
    
    Args:
        v: Vector to project
        normal: Plane normal (should be normalized)
        
    Returns:
        Projected vector on plane
    """
    normal = normalize(normal)
    return v - np.dot(v, normal) * normal


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to range."""
    return np.clip(value, min_val, max_val)


def remap(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """Remap value from one range to another."""
    t = (value - in_min) / (in_max - in_min)
    return out_min + t * (out_max - out_min)
