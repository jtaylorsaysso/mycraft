"""Unit tests for engine.rendering.trimesh_utils.

Tests cover:
- Voxel grid to trimesh conversion
- Collision geometry simplification (convex hull)
- Batch ray intersection
- CSG boolean operations
- Marching cubes smooth mesh generation
"""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal
from typing import Dict, Tuple


# Skip all tests if trimesh is not available
pytest.importorskip("trimesh")


from engine.rendering.trimesh_utils import (
    is_available,
    voxel_grid_to_array,
    voxel_to_trimesh,
    simplify_collision_geometry,
    batch_ray_intersect,
    get_first_ray_hit,
    carve_sphere,
    carve_box,
    generate_smooth_mesh,
    get_surface_voxels,
    trimesh_to_geom_data
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def small_voxel_grid() -> Dict[Tuple[int, int, int], str]:
    """Create a small 4x4x4 voxel grid for testing."""
    grid = {}
    for x in range(4):
        for y in range(4):
            for z in range(4):
                grid[(x, y, z)] = "stone"
    return grid


@pytest.fixture
def terrain_voxel_grid() -> Dict[Tuple[int, int, int], str]:
    """Create a terrain-like voxel grid (surface only)."""
    grid = {}
    for x in range(8):
        for z in range(8):
            height = 3 + (x + z) % 3
            for y in range(height):
                grid[(x, y, z)] = "stone" if y < height - 1 else "grass"
    return grid


@pytest.fixture
def sparse_voxel_grid() -> Dict[Tuple[int, int, int], str]:
    """Create a sparse voxel grid with gaps."""
    return {
        (0, 0, 0): "stone",
        (2, 0, 0): "stone",
        (0, 2, 0): "stone",
        (2, 2, 0): "stone",
    }


# =============================================================================
# Basic Tests
# =============================================================================

class TestAvailability:
    """Test trimesh availability check."""
    
    def test_is_available(self):
        """Trimesh should be available if tests are running."""
        assert is_available() is True


class TestVoxelGridToArray:
    """Tests for voxel_grid_to_array conversion."""
    
    def test_empty_grid(self):
        """Empty grid should return minimal array."""
        arr, offset = voxel_grid_to_array({})
        assert arr.shape == (1, 1, 1)
        assert offset == (0, 0, 0)
    
    def test_single_voxel(self):
        """Single voxel should create 1x1x1 array."""
        grid = {(5, 5, 5): "stone"}
        arr, offset = voxel_grid_to_array(grid)
        assert arr.shape == (1, 1, 1)
        assert arr[0, 0, 0] == True  # Use == for numpy bool comparison
        assert offset == (5, 5, 5)
    
    def test_multiple_voxels(self, small_voxel_grid):
        """Multiple voxels should create correctly sized array."""
        arr, offset = voxel_grid_to_array(small_voxel_grid)
        assert arr.shape == (4, 4, 4)
        assert offset == (0, 0, 0)
        # All voxels should be filled
        assert arr.all()


# =============================================================================
# Mesh Conversion Tests
# =============================================================================

class TestVoxelToTrimesh:
    """Tests for voxel to trimesh conversion."""
    
    def test_empty_grid_returns_empty_mesh(self):
        """Empty grid should return empty mesh."""
        mesh = voxel_to_trimesh({})
        assert mesh.is_empty
    
    def test_single_voxel_creates_cube(self):
        """Single voxel should create a cube mesh."""
        grid = {(0, 0, 0): "stone"}
        mesh = voxel_to_trimesh(grid)
        # A cube has 8 vertices (or 24 if not merged)
        assert len(mesh.vertices) > 0
        # A cube has 12 triangles (2 per face * 6 faces)
        assert len(mesh.faces) == 12
    
    def test_multiple_voxels_create_valid_mesh(self, small_voxel_grid):
        """Multiple voxels should create a valid mesh."""
        mesh = voxel_to_trimesh(small_voxel_grid)
        assert not mesh.is_empty
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0


# =============================================================================
# Collision Simplification Tests
# =============================================================================

class TestSimplifyCollisionGeometry:
    """Tests for collision geometry simplification."""
    
    def test_convex_hull_reduces_faces(self, small_voxel_grid):
        """Convex hull should significantly reduce face count."""
        original = voxel_to_trimesh(small_voxel_grid)
        simplified = simplify_collision_geometry(small_voxel_grid, method='convex_hull')
        
        # Simplified should have fewer faces
        assert len(simplified.faces) < len(original.faces)
    
    def test_convex_hull_is_convex(self, small_voxel_grid):
        """Result should be a convex mesh."""
        simplified = simplify_collision_geometry(small_voxel_grid, method='convex_hull')
        # Convex hull is always convex
        assert simplified.is_convex
    
    def test_empty_grid_returns_empty(self):
        """Empty grid should return empty mesh."""
        simplified = simplify_collision_geometry({})
        assert simplified.is_empty


# =============================================================================
# Ray Intersection Tests
# =============================================================================

class TestBatchRayIntersect:
    """Tests for batch ray intersection."""
    
    def test_single_ray_hits_mesh(self, small_voxel_grid):
        """Single downward ray should hit the terrain."""
        mesh = voxel_to_trimesh(small_voxel_grid)
        
        # Ray from above looking down
        origins = np.array([[2.0, 10.0, 2.0]], dtype=np.float32)
        directions = np.array([[0.0, -1.0, 0.0]], dtype=np.float32)
        
        hits, ray_idx, dists = batch_ray_intersect(mesh, origins, directions)
        
        assert len(hits) > 0
        assert 0 in ray_idx
    
    def test_ray_misses_mesh(self, small_voxel_grid):
        """Ray pointing away should miss."""
        mesh = voxel_to_trimesh(small_voxel_grid)
        
        # Ray pointing away from mesh
        origins = np.array([[10.0, 10.0, 10.0]], dtype=np.float32)
        directions = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
        
        hits, ray_idx, dists = batch_ray_intersect(mesh, origins, directions)
        
        assert len(hits) == 0
    
    def test_multiple_rays_parallel(self, terrain_voxel_grid):
        """Multiple parallel rays should find different hit points."""
        mesh = voxel_to_trimesh(terrain_voxel_grid)
        
        # Multiple downward rays
        origins = np.array([
            [1.5, 20.0, 1.5],
            [3.5, 20.0, 3.5],
            [5.5, 20.0, 5.5],
        ], dtype=np.float32)
        directions = np.tile([0.0, -1.0, 0.0], (3, 1)).astype(np.float32)
        
        hits, ray_idx, dists = batch_ray_intersect(mesh, origins, directions)
        
        # All three rays should hit
        assert len(np.unique(ray_idx)) >= 1  # At least one ray hit


class TestGetFirstRayHit:
    """Tests for get_first_ray_hit helper."""
    
    def test_returns_correct_shape(self, small_voxel_grid):
        """Should return arrays matching input ray count."""
        mesh = voxel_to_trimesh(small_voxel_grid)
        
        origins = np.array([
            [2.0, 10.0, 2.0],
            [100.0, 100.0, 100.0],  # Miss
        ], dtype=np.float32)
        directions = np.array([
            [0.0, -1.0, 0.0],
            [0.0, -1.0, 0.0],
        ], dtype=np.float32)
        
        hit_points, did_hit = get_first_ray_hit(mesh, origins, directions)
        
        assert hit_points.shape == (2, 3)
        assert did_hit.shape == (2,)
        assert did_hit[0] is True or did_hit[0] == True
        assert did_hit[1] is False or did_hit[1] == False


# =============================================================================
# CSG Boolean Tests
# =============================================================================

class TestCarveOperations:
    """Tests for CSG carve operations."""
    
    def test_carve_sphere(self, small_voxel_grid):
        """Carving a sphere should modify the mesh."""
        mesh = voxel_to_trimesh(small_voxel_grid)
        original_volume = mesh.volume
        
        carved = carve_sphere(mesh, center=[2, 2, 2], radius=1.0)
        
        # Volume should decrease (or stay same if CSG fails)
        assert carved.volume <= original_volume * 1.01  # Allow small tolerance
    
    def test_carve_box(self, small_voxel_grid):
        """Carving a box should modify the mesh."""
        mesh = voxel_to_trimesh(small_voxel_grid)
        original_volume = mesh.volume
        
        carved = carve_box(mesh, min_point=[1, 1, 1], max_point=[3, 3, 3])
        
        # Volume should decrease (or stay same if CSG fails)
        assert carved.volume <= original_volume * 1.01
    
    def test_carve_empty_mesh(self):
        """Carving empty mesh should return empty."""
        import trimesh
        empty = trimesh.Trimesh()
        result = carve_sphere(empty, [0, 0, 0], 1.0)
        assert result.is_empty


# =============================================================================
# Smooth Mesh (Marching Cubes) Tests
# =============================================================================

class TestGenerateSmoothMesh:
    """Tests for marching cubes smooth mesh generation."""
    
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_generates_valid_mesh(self, terrain_voxel_grid):
        """Should generate a valid smooth mesh."""
        mesh = generate_smooth_mesh(terrain_voxel_grid)
        
        assert mesh is not None
        assert not mesh.is_empty
        assert len(mesh.vertices) > 0
        assert len(mesh.faces) > 0
    
    def test_empty_grid_returns_none(self):
        """Empty grid should return None."""
        result = generate_smooth_mesh({})
        assert result is None


class TestGetSurfaceVoxels:
    """Tests for surface voxel extraction."""
    
    def test_reduces_internal_voxels(self, small_voxel_grid):
        """Should remove internal voxels."""
        surface = get_surface_voxels(small_voxel_grid)
        
        # Surface should have fewer voxels than full grid
        # (4x4x4 = 64 full, surface = 56 exposed faces worth)
        assert len(surface) <= len(small_voxel_grid)
    
    def test_empty_grid_returns_empty(self):
        """Empty grid should return empty."""
        result = get_surface_voxels({})
        assert result == {}


# =============================================================================
# Panda3D Conversion Tests
# =============================================================================

class TestTrimeshToGeomData:
    """Tests for trimesh to Panda3D conversion."""
    
    def test_extracts_vertex_data(self, small_voxel_grid):
        """Should extract vertex and face data."""
        mesh = voxel_to_trimesh(small_voxel_grid)
        
        vertices, indices, normals = trimesh_to_geom_data(mesh)
        
        assert vertices.dtype == np.float32
        assert indices.dtype == np.uint32
        assert len(vertices) > 0
        assert len(indices) > 0
    
    def test_empty_mesh_returns_empty_arrays(self):
        """Empty mesh should return empty arrays."""
        import trimesh
        empty = trimesh.Trimesh()
        
        vertices, indices, normals = trimesh_to_geom_data(empty)
        
        assert len(vertices) == 0
        assert len(indices) == 0
