"""NumPy-based mesh utilities for voxel terrain generation.

Provides optimized batch operations for mesh construction that can be
integrated with the existing MeshBuilder where beneficial.

Key insight from benchmarking: NumPy provides significant benefit when:
1. Processing arrays of pre-collected data (not during iteration)
2. Performing batch transformations on vertex arrays
3. Generating final vertex/index buffers for GPU upload

For best results, collect data first, then batch process with NumPy.
"""

import numpy as np
from numpy.typing import NDArray
from typing import Tuple, List, Optional


# Type aliases
Vec3 = NDArray[np.float32]  # (3,)
Vec3Array = NDArray[np.float32]  # (N, 3)
IndexArray = NDArray[np.uint32]  # (N,)


# Pre-computed face data for voxel meshing
# Face order: top, bottom, north, south, east, west
FACE_DIRECTIONS = np.array([
    [0, 1, 0],   # top (+Y)
    [0, -1, 0],  # bottom (-Y)
    [0, 0, -1],  # north (-Z)
    [0, 0, 1],   # south (+Z)
    [1, 0, 0],   # east (+X)
    [-1, 0, 0],  # west (-X)
], dtype=np.int32)

# Vertex offsets for each face (4 vertices per face)
# In Panda3D coordinates: (X, Z_world, Y_height)
FACE_VERTEX_OFFSETS = np.array([
    # top (y+1 plane)
    [[0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]],
    # bottom (y plane)
    [[0, 1, 0], [1, 1, 0], [1, 0, 0], [0, 0, 0]],
    # north (-z face)
    [[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]],
    # south (+z face)
    [[1, 1, 0], [0, 1, 0], [0, 1, 1], [1, 1, 1]],
    # east (+x face)
    [[1, 0, 0], [1, 1, 0], [1, 1, 1], [1, 0, 1]],
    # west (-x face)
    [[0, 1, 0], [0, 0, 0], [0, 0, 1], [0, 1, 1]],
], dtype=np.float32)


def batch_generate_face_vertices(
    positions: Vec3Array,
    face_indices: NDArray[np.int32]
) -> Vec3Array:
    """Generate vertices for multiple faces in batch.
    
    Args:
        positions: Block positions (N, 3) as [x, y, z]
        face_indices: Face type index (N,) - 0=top, 1=bottom, etc.
        
    Returns:
        Vertices array (N*4, 3) in Panda3D coordinates [x, z, y]
    """
    n_faces = len(positions)
    vertices = np.empty((n_faces * 4, 3), dtype=np.float32)
    
    for i in range(n_faces):
        x, y, z = positions[i]
        face_idx = face_indices[i]
        offsets = FACE_VERTEX_OFFSETS[face_idx]
        
        # Convert to Panda3D coords: (x, z, y)
        base_idx = i * 4
        for j in range(4):
            vertices[base_idx + j, 0] = x + offsets[j, 0]  # X
            vertices[base_idx + j, 1] = z + offsets[j, 1]  # Z (world depth)
            vertices[base_idx + j, 2] = y + offsets[j, 2]  # Y (height)
    
    return vertices


def batch_generate_face_indices(num_faces: int, start_vertex: int = 0) -> IndexArray:
    """Generate triangle indices for a batch of quads.
    
    Args:
        num_faces: Number of quad faces
        start_vertex: Starting vertex index
        
    Returns:
        Indices array (num_faces * 6,) for triangles
    """
    indices = np.empty(num_faces * 6, dtype=np.uint32)
    
    for i in range(num_faces):
        v = start_vertex + i * 4
        idx = i * 6
        # First triangle
        indices[idx] = v
        indices[idx + 1] = v + 1
        indices[idx + 2] = v + 2
        # Second triangle  
        indices[idx + 3] = v
        indices[idx + 4] = v + 2
        indices[idx + 5] = v + 3
    
    return indices


def batch_generate_face_indices_vectorized(num_faces: int, start_vertex: int = 0) -> IndexArray:
    """Vectorized index generation (faster for large meshes).
    
    Args:
        num_faces: Number of quad faces
        start_vertex: Starting vertex index
        
    Returns:
        Indices array (num_faces * 6,) for triangles
    """
    # Generate base indices for one face: [0,1,2, 0,2,3]
    base = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
    
    # Create offsets for each face
    offsets = np.arange(num_faces, dtype=np.uint32) * 4 + start_vertex
    
    # Broadcast to create all indices
    return (base[np.newaxis, :] + offsets[:, np.newaxis]).flatten()


def compute_ao_batch(
    heights: NDArray[np.int32],
    chunk_size: int
) -> NDArray[np.float32]:
    """Compute ambient occlusion for entire chunk at once.
    
    Args:
        heights: 2D height array (chunk_size, chunk_size)
        chunk_size: Size of chunk
        
    Returns:
        AO values (chunk_size, chunk_size, 4) for each corner
    """
    # Pad heights for neighbor lookups
    padded = np.pad(heights, 1, mode='edge')
    
    ao = np.ones((chunk_size, chunk_size, 4), dtype=np.float32)
    
    for x in range(chunk_size):
        for z in range(chunk_size):
            h = heights[x, z]
            px, pz = x + 1, z + 1  # Padded indices
            
            # Corner 0 (0,0)
            count = 0
            if padded[px-1, pz] >= h: count += 1
            if padded[px, pz-1] >= h: count += 1
            if padded[px-1, pz-1] >= h: count += 1
            ao[x, z, 0] = 1.0 - min(3, count) * 0.2
            
            # Corner 1 (1,0)
            count = 0
            if padded[px+1, pz] >= h: count += 1
            if padded[px, pz-1] >= h: count += 1
            if padded[px+1, pz-1] >= h: count += 1
            ao[x, z, 1] = 1.0 - min(3, count) * 0.2
            
            # Corner 2 (1,1)
            count = 0
            if padded[px+1, pz] >= h: count += 1
            if padded[px, pz+1] >= h: count += 1
            if padded[px+1, pz+1] >= h: count += 1
            ao[x, z, 2] = 1.0 - min(3, count) * 0.2
            
            # Corner 3 (0,1)
            count = 0
            if padded[px-1, pz] >= h: count += 1
            if padded[px, pz+1] >= h: count += 1
            if padded[px-1, pz+1] >= h: count += 1
            ao[x, z, 3] = 1.0 - min(3, count) * 0.2
    
    return ao


def heights_to_voxel_array(heights: NDArray[np.int32]) -> NDArray[np.bool_]:
    """Convert heightmap to 3D voxel occupancy array.
    
    Args:
        heights: 2D height array (width, depth)
        
    Returns:
        3D boolean array (width, height, depth) where True = solid
    """
    width, depth = heights.shape
    max_height = int(heights.max()) + 1
    
    voxels = np.zeros((width, max_height, depth), dtype=np.bool_)
    
    for x in range(width):
        for z in range(depth):
            h = heights[x, z]
            voxels[x, :h, z] = True
    
    return voxels


def find_exposed_faces_from_array(voxels: NDArray[np.bool_]) -> Tuple[Vec3Array, NDArray[np.int32]]:
    """Find all exposed faces from a 3D voxel array.
    
    Args:
        voxels: 3D boolean occupancy array (width, height, depth)
        
    Returns:
        Tuple of (positions, face_indices) for exposed faces
    """
    width, height, depth = voxels.shape
    
    # Pad with False (air) on all sides
    padded = np.pad(voxels, 1, mode='constant', constant_values=False)
    
    positions = []
    face_indices = []
    
    for x in range(width):
        for y in range(height):
            for z in range(depth):
                if not voxels[x, y, z]:
                    continue
                
                px, py, pz = x + 1, y + 1, z + 1
                
                # Check each face direction
                for face_idx, (dx, dy, dz) in enumerate(FACE_DIRECTIONS):
                    if not padded[px + dx, py + dy, pz + dz]:
                        positions.append([x, y, z])
                        face_indices.append(face_idx)
    
    return (
        np.array(positions, dtype=np.float32) if positions else np.empty((0, 3), dtype=np.float32),
        np.array(face_indices, dtype=np.int32) if face_indices else np.empty(0, dtype=np.int32)
    )


def create_vertex_buffer(
    vertices: Vec3Array,
    colors: Optional[NDArray[np.float32]] = None,
    uvs: Optional[NDArray[np.float32]] = None
) -> NDArray[np.float32]:
    """Create interleaved vertex buffer for GPU upload.
    
    Args:
        vertices: Vertex positions (N, 3)
        colors: Vertex colors (N, 4) or None for white
        uvs: Texture coordinates (N, 2) or None for zeros
        
    Returns:
        Interleaved buffer (N, 9) as [x,y,z, r,g,b,a, u,v]
    """
    n = len(vertices)
    
    if colors is None:
        colors = np.ones((n, 4), dtype=np.float32)
    if uvs is None:
        uvs = np.zeros((n, 2), dtype=np.float32)
    
    buffer = np.empty((n, 9), dtype=np.float32)
    buffer[:, 0:3] = vertices
    buffer[:, 3:7] = colors
    buffer[:, 7:9] = uvs
    
    return buffer


# =============================================================================
# Smooth Terrain Generation (Marching Cubes)
# =============================================================================

def generate_smooth_terrain_mesh(
    heights: NDArray[np.int32],
    chunk_size: int = 16,
    max_height: Optional[int] = None
) -> Tuple[Vec3Array, IndexArray, Optional[Vec3Array]]:
    """Generate smooth terrain mesh using marching cubes.
    
    Converts a 2D heightmap to a smooth 3D terrain surface using
    trimesh's marching cubes algorithm. Produces organic-looking
    terrain instead of blocky voxels.
    
    Requires: trimesh with scikit-image optional dependency.
    
    Args:
        heights: 2D height array (chunk_size, chunk_size)
        chunk_size: Size of chunk (default 16)
        max_height: Maximum height to include (default: max(heights) + 2)
        
    Returns:
        Tuple of (vertices, indices, normals):
        - vertices: (N, 3) float32 in Panda3D coordinates [x, z, y]
        - indices: (M,) uint32 triangle indices
        - normals: (N, 3) float32 vertex normals, or None if unavailable
        
    Example:
        >>> heights = np.random.randint(5, 10, (16, 16))
        >>> verts, idxs, norms = generate_smooth_terrain_mesh(heights)
        >>> print(f"Generated {len(verts)} vertices")
    """
    try:
        import trimesh
        from trimesh import voxel as tv
    except ImportError:
        raise ImportError("trimesh with scikit-image is required for smooth terrain")
    
    if max_height is None:
        max_height = int(heights.max()) + 2
    
    # Create 3D voxel array from heightmap
    width, depth = heights.shape
    voxel_array = np.zeros((width, max_height, depth), dtype=np.bool_)
    
    for x in range(width):
        for z in range(depth):
            h = heights[x, z]
            voxel_array[x, :h, z] = True
    
    # Pad with zeros for proper marching cubes boundary
    padded = np.pad(voxel_array, 1, mode='constant', constant_values=False)
    
    try:
        # Create VoxelGrid and run marching cubes
        vg = tv.VoxelGrid(tv.encoding.DenseEncoding(padded))
        mesh = vg.marching_cubes
        
        # Adjust for padding offset (-1 in each dimension)
        mesh.apply_translation([-1, -1, -1])
        
        # Extract vertex data
        # Note: trimesh uses XYZ, we need XZY for Panda3D
        vertices_xyz = mesh.vertices.astype(np.float32)
        vertices_xzy = np.column_stack([
            vertices_xyz[:, 0],  # X stays X
            vertices_xyz[:, 2],  # Z becomes Y (depth)
            vertices_xyz[:, 1]   # Y becomes Z (height)
        ])
        
        indices = mesh.faces.flatten().astype(np.uint32)
        
        # Get normals if available
        try:
            normals_xyz = mesh.vertex_normals.astype(np.float32)
            normals_xzy = np.column_stack([
                normals_xyz[:, 0],
                normals_xyz[:, 2],
                normals_xyz[:, 1]
            ])
        except Exception:
            normals_xzy = None
        
        return vertices_xzy, indices, normals_xzy
        
    except ImportError:
        raise ImportError("marching_cubes requires scikit-image")
    except Exception as e:
        raise RuntimeError(f"Marching cubes failed: {e}")

