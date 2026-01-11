"""Benchmarks comparing Python list-based vs NumPy mesh generation.

Run with: pytest tests/benchmarks/test_numpy_mesh.py -v --benchmark-only
"""

import pytest
import numpy as np
from typing import Dict, Tuple, List


class MockBlockDef:
    """Minimal block definition for benchmarking."""
    def get_face_tile(self, face: str) -> int:
        return 0


class MockBlockRegistry:
    """Minimal block registry for benchmarking."""
    @staticmethod
    def get_block(name: str) -> MockBlockDef:
        return MockBlockDef()


def generate_test_voxel_grid(size: int = 16) -> Dict[Tuple[int, int, int], str]:
    """Generate a test voxel grid (sparse dict) for benchmarking."""
    grid = {}
    # Create terrain-like pattern (only top surface + some depth)
    for x in range(size):
        for z in range(size):
            # Height varies between 5-8
            height = 5 + (x + z) % 4
            for y in range(height - 2, height + 1):
                grid[(x, y, z)] = "stone" if y < height else "grass"
    return grid


@pytest.fixture
def small_grid():
    """8x8x8 voxel grid for quick tests."""
    return generate_test_voxel_grid(8)


@pytest.fixture
def medium_grid():
    """16x16 chunk grid for realistic tests."""
    return generate_test_voxel_grid(16)


@pytest.fixture
def large_grid():
    """32x32 double-chunk grid for stress tests."""
    return generate_test_voxel_grid(32)


# =============================================================================
# Legacy (Python loop) implementation for comparison
# =============================================================================

def build_mesh_legacy(voxel_grid: dict, chunk_size: int = 16) -> Tuple[List, List]:
    """Legacy Python-loop mesh generation (for comparison).
    
    Returns tuple of (vertices, indices) as Python lists.
    """
    vertices = []
    indices = []
    index = 0
    
    directions = [
        (0, 1, 0, 'top'),
        (0, -1, 0, 'bottom'),
        (0, 0, -1, 'north'),
        (0, 0, 1, 'south'),
        (1, 0, 0, 'east'),
        (-1, 0, 0, 'west')
    ]
    
    # Face vertex offsets (relative to block position)
    face_offsets = {
        'top': [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
        'bottom': [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)],
        'north': [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
        'south': [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)],
        'east': [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
        'west': [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)],
    }
    
    for pos, block_name in voxel_grid.items():
        x, y, z = pos
        
        for dx, dy, dz, face_name in directions:
            neighbor_pos = (x + dx, y + dy, z + dz)
            if neighbor_pos in voxel_grid:
                continue
            
            # Add face vertices
            offsets = face_offsets[face_name]
            for ox, oz, oy in offsets:  # Note: swapped for Panda3D coords
                vertices.extend([x + ox, z + oz, y + oy])
            
            # Add face indices (two triangles)
            indices.extend([index, index + 1, index + 2])
            indices.extend([index, index + 2, index + 3])
            index += 4
    
    return vertices, indices


# =============================================================================
# NumPy-optimized implementation
# =============================================================================

def build_mesh_numpy(voxel_grid: dict, chunk_size: int = 16) -> Tuple[np.ndarray, np.ndarray]:
    """NumPy-optimized mesh generation.
    
    Returns tuple of (vertices, indices) as NumPy arrays.
    """
    if not voxel_grid:
        return np.array([], dtype=np.float32), np.array([], dtype=np.uint32)
    
    # Pre-calculate exposed faces
    directions = np.array([
        [0, 1, 0],   # top
        [0, -1, 0],  # bottom
        [0, 0, -1],  # north
        [0, 0, 1],   # south
        [1, 0, 0],   # east
        [-1, 0, 0],  # west
    ], dtype=np.int32)
    
    # Face vertex offsets (4 vertices per face, XZY order for Panda3D)
    face_offsets = np.array([
        # top (y+1)
        [[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]],
        # bottom (y)
        [[0, 1, 0], [1, 1, 0], [1, 0, 0], [0, 0, 0]],
        # north (z)
        [[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]],
        # south (z+1)
        [[1, 1, 0], [0, 1, 0], [0, 1, 1], [1, 1, 1]],
        # east (x+1)
        [[1, 0, 0], [1, 1, 0], [1, 1, 1], [1, 0, 1]],
        # west (x)
        [[0, 1, 0], [0, 0, 0], [0, 0, 1], [0, 1, 1]],
    ], dtype=np.float32)
    
    # Convert grid to arrays
    positions = np.array(list(voxel_grid.keys()), dtype=np.int32)
    position_set = set(voxel_grid.keys())
    
    # Count exposed faces
    exposed_faces = []
    for i, pos in enumerate(positions):
        x, y, z = pos
        for face_idx, (dx, dy, dz) in enumerate(directions):
            neighbor = (x + dx, y + dy, z + dz)
            if neighbor not in position_set:
                exposed_faces.append((i, face_idx))
    
    if not exposed_faces:
        return np.array([], dtype=np.float32), np.array([], dtype=np.uint32)
    
    num_faces = len(exposed_faces)
    
    # Pre-allocate output arrays
    vertices = np.empty((num_faces * 4, 3), dtype=np.float32)
    indices = np.empty((num_faces * 2, 3), dtype=np.uint32)
    
    # Build mesh in batches
    for face_num, (block_idx, face_idx) in enumerate(exposed_faces):
        pos = positions[block_idx]
        x, y, z = pos
        
        # Get face vertex offsets and add block position
        # Note: We swap Y and Z for Panda3D (XZY convention)
        offsets = face_offsets[face_idx]
        verts = np.array([
            [x + offsets[i, 0], z + offsets[i, 1], y + offsets[i, 2]]
            for i in range(4)
        ], dtype=np.float32)
        
        v_start = face_num * 4
        vertices[v_start:v_start + 4] = verts
        
        # Build indices
        i_start = face_num * 2
        indices[i_start] = [v_start, v_start + 1, v_start + 2]
        indices[i_start + 1] = [v_start, v_start + 2, v_start + 3]
    
    return vertices.flatten(), indices.flatten()


# =============================================================================
# Benchmarks
# =============================================================================

def test_mesh_legacy_small(benchmark, small_grid):
    """Benchmark legacy mesh generation on small grid."""
    result = benchmark(build_mesh_legacy, small_grid, 8)
    assert len(result[0]) > 0


def test_mesh_numpy_small(benchmark, small_grid):
    """Benchmark NumPy mesh generation on small grid."""
    result = benchmark(build_mesh_numpy, small_grid, 8)
    assert len(result[0]) > 0


def test_mesh_legacy_medium(benchmark, medium_grid):
    """Benchmark legacy mesh generation on medium grid."""
    result = benchmark(build_mesh_legacy, medium_grid, 16)
    assert len(result[0]) > 0


def test_mesh_numpy_medium(benchmark, medium_grid):
    """Benchmark NumPy mesh generation on medium grid."""
    result = benchmark(build_mesh_numpy, medium_grid, 16)
    assert len(result[0]) > 0


def test_mesh_legacy_large(benchmark, large_grid):
    """Benchmark legacy mesh generation on large grid."""
    result = benchmark(build_mesh_legacy, large_grid, 32)
    assert len(result[0]) > 0


def test_mesh_numpy_large(benchmark, large_grid):
    """Benchmark NumPy mesh generation on large grid."""
    result = benchmark(build_mesh_numpy, large_grid, 32)
    assert len(result[0]) > 0


# =============================================================================
# Correctness test
# =============================================================================

def test_numpy_matches_legacy():
    """Verify NumPy version produces same vertex count as legacy."""
    grid = generate_test_voxel_grid(8)
    
    legacy_verts, legacy_idx = build_mesh_legacy(grid, 8)
    numpy_verts, numpy_idx = build_mesh_numpy(grid, 8)
    
    # Should have same number of vertices and indices
    assert len(legacy_verts) == len(numpy_verts), f"Vertex count mismatch: {len(legacy_verts)} vs {len(numpy_verts)}"
    assert len(legacy_idx) == len(numpy_idx), f"Index count mismatch: {len(legacy_idx)} vs {len(numpy_idx)}"
