"""Trimesh-based mesh utilities for voxel terrain and collision.

Provides advanced mesh operations using the trimesh library:
- Convex hull collision simplification
- Marching cubes for smooth terrain
- CSG boolean operations for cave/explosion carving
- Batch ray intersection for AI and physics

Requires optional dependencies: scikit-image, scipy, rtree, manifold3d
"""

import numpy as np
from numpy.typing import NDArray
from typing import Dict, Tuple, List, Optional, Any

try:
    import trimesh
    from trimesh import voxel as tv
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False
    trimesh = None
    tv = None


# Type aliases
Vec3 = NDArray[np.float32]  # (3,)
Vec3Array = NDArray[np.float32]  # (N, 3)


def is_available() -> bool:
    """Check if trimesh is available."""
    return TRIMESH_AVAILABLE


def voxel_grid_to_array(
    voxel_grid: Dict[Tuple[int, int, int], str],
    chunk_size: int = 16
) -> Tuple[NDArray[np.bool_], Tuple[int, int, int]]:
    """Convert sparse voxel grid dictionary to 3D numpy array.
    
    Args:
        voxel_grid: Dict mapping (x, y, z) positions to block names
        chunk_size: Expected chunk size (default 16)
        
    Returns:
        Tuple of (3D boolean array, (min_x, min_y, min_z) offset)
    """
    if not voxel_grid:
        return np.zeros((1, 1, 1), dtype=np.bool_), (0, 0, 0)
    
    # Find bounds
    positions = np.array(list(voxel_grid.keys()), dtype=np.int32)
    min_pos = positions.min(axis=0)
    max_pos = positions.max(axis=0)
    
    # Create array with size to fit all voxels
    size = max_pos - min_pos + 1
    voxel_array = np.zeros(size, dtype=np.bool_)
    
    # Fill array
    for pos in voxel_grid.keys():
        local = np.array(pos, dtype=np.int32) - min_pos
        voxel_array[local[0], local[1], local[2]] = True
    
    return voxel_array, tuple(min_pos)


def voxel_to_trimesh(
    voxel_grid: Dict[Tuple[int, int, int], str],
    chunk_size: int = 16
) -> 'trimesh.Trimesh':
    """Convert voxel grid dictionary to trimesh mesh.
    
    Creates a mesh where each voxel is represented as a unit cube.
    The mesh is positioned based on the voxel coordinates.
    
    Args:
        voxel_grid: Dict mapping (x, y, z) positions to block names
        chunk_size: Expected chunk size (default 16)
        
    Returns:
        trimesh.Trimesh mesh object
        
    Raises:
        ImportError: If trimesh is not available
    """
    if not TRIMESH_AVAILABLE:
        raise ImportError("trimesh is required for voxel_to_trimesh")
    
    if not voxel_grid:
        # Return empty mesh
        return trimesh.Trimesh()
    
    # Convert to dense array
    voxel_array, offset = voxel_grid_to_array(voxel_grid, chunk_size)
    
    # Create VoxelGrid from array
    vg = tv.VoxelGrid(tv.encoding.DenseEncoding(voxel_array))
    
    # Convert to box mesh (each voxel = cube)
    mesh = vg.as_boxes()
    
    # Apply offset to position mesh correctly
    mesh.apply_translation(offset)
    
    return mesh


def simplify_collision_geometry(
    voxel_grid: Dict[Tuple[int, int, int], str],
    chunk_size: int = 16,
    method: str = 'convex_hull'
) -> 'trimesh.Trimesh':
    """Generate simplified collision geometry from voxel grid.
    
    Creates a simplified mesh suitable for collision detection.
    The convex hull method provides massive face reduction (typically 99%+)
    but may not be suitable for concave terrain.
    
    Args:
        voxel_grid: Dict mapping (x, y, z) positions to block names
        chunk_size: Expected chunk size (default 16)
        method: Simplification method ('convex_hull' or 'box')
        
    Returns:
        Simplified trimesh.Trimesh for collision
        
    Example:
        >>> grid = {(0,0,0): 'stone', (1,0,0): 'stone'}
        >>> collision_mesh = simplify_collision_geometry(grid)
        >>> print(f"Simplified to {len(collision_mesh.faces)} faces")
    """
    if not TRIMESH_AVAILABLE:
        raise ImportError("trimesh is required for simplify_collision_geometry")
    
    mesh = voxel_to_trimesh(voxel_grid, chunk_size)
    
    if mesh.is_empty:
        return mesh
    
    if method == 'convex_hull':
        return mesh.convex_hull
    else:
        # Return bounding box as 12-face mesh
        return mesh.bounding_box
    

def batch_ray_intersect(
    mesh: 'trimesh.Trimesh',
    origins: Vec3Array,
    directions: Vec3Array
) -> Tuple[Vec3Array, NDArray[np.int32], NDArray[np.float32]]:
    """Perform batch ray intersection against a mesh.
    
    Much faster than per-ray queries for AI line-of-sight,
    projectile prediction, or ground height sampling.
    
    Args:
        mesh: trimesh.Trimesh to intersect against
        origins: Ray origins (N, 3)
        directions: Ray directions (N, 3) - should be normalized
        
    Returns:
        Tuple of:
        - hit_locations: World positions of hits (M, 3)
        - ray_indices: Which ray each hit belongs to (M,)
        - distances: Distance from origin to hit (M,)
        
    Example:
        >>> # Sample ground height at 100 positions
        >>> origins = np.column_stack([x_coords, np.full(100, 50.0), z_coords])
        >>> directions = np.tile([0, -1, 0], (100, 1))
        >>> hits, ray_idx, dists = batch_ray_intersect(terrain, origins, directions)
        >>> ground_heights = origins[ray_idx, 1] - dists
    """
    if not TRIMESH_AVAILABLE:
        raise ImportError("trimesh is required for batch_ray_intersect")
    
    if mesh.is_empty:
        return (
            np.empty((0, 3), dtype=np.float32),
            np.empty(0, dtype=np.int32),
            np.empty(0, dtype=np.float32)
        )
    
    # Perform intersection
    locations, ray_indices, tri_indices = mesh.ray.intersects_location(
        ray_origins=origins.astype(np.float64),
        ray_directions=directions.astype(np.float64)
    )
    
    # Calculate distances
    if len(locations) > 0:
        origin_hits = origins[ray_indices]
        distances = np.linalg.norm(locations - origin_hits, axis=1)
    else:
        distances = np.empty(0, dtype=np.float32)
    
    return (
        locations.astype(np.float32),
        ray_indices.astype(np.int32),
        distances.astype(np.float32)
    )


def get_first_ray_hit(
    mesh: 'trimesh.Trimesh',
    origins: Vec3Array,
    directions: Vec3Array
) -> Tuple[Vec3Array, NDArray[np.bool_]]:
    """Get the first (closest) hit for each ray.
    
    Args:
        mesh: trimesh.Trimesh to intersect against
        origins: Ray origins (N, 3)
        directions: Ray directions (N, 3)
        
    Returns:
        Tuple of:
        - hit_points: Position of first hit per ray (N, 3), NaN for misses
        - did_hit: Boolean mask of which rays hit (N,)
    """
    if not TRIMESH_AVAILABLE:
        raise ImportError("trimesh is required for get_first_ray_hit")
    
    n_rays = len(origins)
    hit_points = np.full((n_rays, 3), np.nan, dtype=np.float32)
    did_hit = np.zeros(n_rays, dtype=np.bool_)
    
    if mesh.is_empty:
        return hit_points, did_hit
    
    locations, ray_indices, distances = batch_ray_intersect(mesh, origins, directions)
    
    if len(locations) == 0:
        return hit_points, did_hit
    
    # For each ray, find the closest hit
    for i in range(n_rays):
        ray_mask = ray_indices == i
        if ray_mask.any():
            ray_dists = distances[ray_mask]
            ray_locs = locations[ray_mask]
            closest_idx = np.argmin(ray_dists)
            hit_points[i] = ray_locs[closest_idx]
            did_hit[i] = True
    
    return hit_points, did_hit


# =============================================================================
# CSG Boolean Operations
# =============================================================================

def carve_sphere(
    mesh: 'trimesh.Trimesh',
    center: Vec3,
    radius: float,
    subdivisions: int = 2
) -> 'trimesh.Trimesh':
    """Subtract a sphere from a mesh (for caves, explosions).
    
    Uses CSG boolean difference operation.
    Requires manifold3d library.
    
    Args:
        mesh: Source mesh to carve
        center: Center of sphere to subtract
        radius: Radius of sphere
        subdivisions: Icosphere subdivisions (higher = smoother)
        
    Returns:
        Carved mesh with sphere removed
        
    Example:
        >>> terrain = voxel_to_trimesh(chunk_grid)
        >>> explosion_pos = [10, 5, 10]
        >>> carved = carve_sphere(terrain, explosion_pos, radius=3.0)
    """
    if not TRIMESH_AVAILABLE:
        raise ImportError("trimesh is required for carve_sphere")
    
    if mesh.is_empty:
        return mesh
    
    # Create sphere at origin then translate
    sphere = trimesh.creation.icosphere(radius=radius, subdivisions=subdivisions)
    sphere.apply_translation(center)
    
    try:
        result = mesh.difference(sphere)
        return result
    except Exception as e:
        # CSG can fail on non-manifold meshes
        # Fall back to returning original
        print(f"CSG carve_sphere failed: {e}")
        return mesh


def carve_box(
    mesh: 'trimesh.Trimesh',
    min_point: Vec3,
    max_point: Vec3
) -> 'trimesh.Trimesh':
    """Subtract a box from a mesh (for mining, room carving).
    
    Uses CSG boolean difference operation.
    Requires manifold3d library.
    
    Args:
        mesh: Source mesh to carve
        min_point: Minimum corner of box
        max_point: Maximum corner of box
        
    Returns:
        Carved mesh with box removed
    """
    if not TRIMESH_AVAILABLE:
        raise ImportError("trimesh is required for carve_box")
    
    if mesh.is_empty:
        return mesh
    
    # Calculate box dimensions and center
    min_pt = np.asarray(min_point)
    max_pt = np.asarray(max_point)
    extents = max_pt - min_pt
    center = (min_pt + max_pt) / 2
    
    # Create box
    box = trimesh.creation.box(extents=extents)
    box.apply_translation(center)
    
    try:
        result = mesh.difference(box)
        return result
    except Exception as e:
        print(f"CSG carve_box failed: {e}")
        return mesh


# =============================================================================
# Marching Cubes for Smooth Terrain
# =============================================================================

def generate_smooth_mesh(
    voxel_grid: Dict[Tuple[int, int, int], str],
    chunk_size: int = 16
) -> Optional['trimesh.Trimesh']:
    """Generate a smooth mesh from voxels using marching cubes.
    
    Creates organic-looking terrain instead of blocky voxels.
    Useful for caves, underwater areas, or natural terrain.
    Requires scikit-image library.
    
    Args:
        voxel_grid: Dict mapping (x, y, z) positions to block names
        chunk_size: Expected chunk size (default 16)
        
    Returns:
        Smooth trimesh.Trimesh or None if failed
        
    Example:
        >>> cave_mesh = generate_smooth_mesh(cave_voxels)
        >>> if cave_mesh:
        ...     print(f"Generated {len(cave_mesh.faces)} smooth faces")
    """
    if not TRIMESH_AVAILABLE:
        raise ImportError("trimesh is required for generate_smooth_mesh")
    
    if not voxel_grid:
        return None
    
    # Convert to dense array
    voxel_array, offset = voxel_grid_to_array(voxel_grid, chunk_size)
    
    # Pad with zeros for proper marching cubes boundary
    padded = np.pad(voxel_array, 1, mode='constant', constant_values=False)
    
    try:
        # Create VoxelGrid and run marching cubes
        vg = tv.VoxelGrid(tv.encoding.DenseEncoding(padded))
        mesh = vg.marching_cubes
        
        # Adjust offset for padding
        adjusted_offset = np.array(offset) - 1
        mesh.apply_translation(adjusted_offset)
        
        return mesh
    except ImportError:
        print("marching_cubes requires scikit-image")
        return None
    except Exception as e:
        print(f"generate_smooth_mesh failed: {e}")
        return None


def get_surface_voxels(
    voxel_grid: Dict[Tuple[int, int, int], str]
) -> Dict[Tuple[int, int, int], str]:
    """Extract only surface (exposed) voxels from a grid.
    
    Reduces voxel count by removing internal voxels that have
    all 6 neighbors filled. Useful for collision optimization.
    Requires scipy library.
    
    Args:
        voxel_grid: Full voxel grid
        
    Returns:
        Filtered grid with only surface voxels
    """
    if not TRIMESH_AVAILABLE:
        raise ImportError("trimesh is required for get_surface_voxels")
    
    if not voxel_grid:
        return {}
    
    # Convert to dense array
    voxel_array, offset = voxel_grid_to_array(voxel_grid)
    
    try:
        # Create VoxelGrid and hollow it
        vg = tv.VoxelGrid(tv.encoding.DenseEncoding(voxel_array))
        hollow = vg.hollow()
        
        # Convert back to dictionary
        result = {}
        filled_indices = hollow.sparse_indices
        offset_arr = np.array(offset, dtype=np.int32)
        
        for idx in filled_indices:
            world_pos = tuple(idx + offset_arr)
            if world_pos in voxel_grid:
                result[world_pos] = voxel_grid[world_pos]
        
        return result
    except ImportError:
        print("hollow() requires scipy")
        return voxel_grid
    except Exception as e:
        print(f"get_surface_voxels failed: {e}")
        return voxel_grid


# =============================================================================
# Mesh to Panda3D Conversion
# =============================================================================

def trimesh_to_geom_data(
    mesh: 'trimesh.Trimesh'
) -> Tuple[NDArray[np.float32], NDArray[np.uint32], Optional[NDArray[np.float32]]]:
    """Extract vertex and face data for Panda3D GeomNode creation.
    
    Args:
        mesh: trimesh.Trimesh to convert
        
    Returns:
        Tuple of (vertices, indices, normals):
        - vertices: (N, 3) float32 vertex positions
        - indices: (M,) uint32 triangle indices
        - normals: (N, 3) float32 vertex normals or None
    """
    if not TRIMESH_AVAILABLE:
        raise ImportError("trimesh is required")
    
    if mesh.is_empty:
        return (
            np.empty((0, 3), dtype=np.float32),
            np.empty(0, dtype=np.uint32),
            None
        )
    
    vertices = mesh.vertices.astype(np.float32)
    indices = mesh.faces.flatten().astype(np.uint32)
    
    try:
        normals = mesh.vertex_normals.astype(np.float32)
    except Exception:
        normals = None
    
    return vertices, indices, normals
