"""Benchmarks for noise generation (scalar vs vectorized)."""

import pytest
import numpy as np
from engine.world.noise import PerlinNoise2D, get_noise, get_noise_grid


@pytest.fixture
def noise_gen():
    return PerlinNoise2D(seed=42)


# =============================================================================
# Scalar (per-point) benchmarks
# =============================================================================

def test_noise_scalar_single(benchmark, noise_gen):
    """Benchmark single point noise."""
    benchmark(noise_gen.noise, 10.5, 20.3)


def test_noise_scalar_chunk_16x16(benchmark, noise_gen):
    """Benchmark scalar noise for 16x16 chunk (256 calls)."""
    def generate_chunk():
        result = []
        for x in range(16):
            row = []
            for z in range(16):
                row.append(noise_gen.noise(x * 0.1, z * 0.1))
            result.append(row)
        return result
    
    benchmark(generate_chunk)


def test_noise_octave_scalar_chunk_16x16(benchmark, noise_gen):
    """Benchmark octave noise for 16x16 chunk (256 calls)."""
    def generate_chunk():
        result = []
        for x in range(16):
            row = []
            for z in range(16):
                row.append(noise_gen.octave_noise(x * 0.1, z * 0.1, octaves=4))
            result.append(row)
        return result
    
    benchmark(generate_chunk)


# =============================================================================
# Vectorized (NumPy) benchmarks
# =============================================================================

def test_noise_vectorized_chunk_16x16(benchmark, noise_gen):
    """Benchmark vectorized noise for 16x16 chunk (single call)."""
    benchmark(noise_gen.noise_grid, 0, 0, 16, 16, 0.1)


def test_noise_octave_vectorized_chunk_16x16(benchmark, noise_gen):
    """Benchmark vectorized octave noise for 16x16 chunk (single call)."""
    benchmark(noise_gen.octave_noise_grid, 0, 0, 16, 16, 0.1, 4)


def test_noise_vectorized_chunk_32x32(benchmark, noise_gen):
    """Benchmark vectorized noise for 32x32 chunk."""
    benchmark(noise_gen.noise_grid, 0, 0, 32, 32, 0.1)


def test_noise_octave_vectorized_chunk_32x32(benchmark, noise_gen):
    """Benchmark vectorized octave noise for 32x32 chunk."""
    benchmark(noise_gen.octave_noise_grid, 0, 0, 32, 32, 0.1, 4)


# =============================================================================
# Correctness tests
# =============================================================================

def test_vectorized_matches_scalar():
    """Verify vectorized produces same results as scalar."""
    noise = PerlinNoise2D(seed=12345)
    
    # Test single octave
    for x in range(4):
        for z in range(4):
            scalar = noise.noise(x * 0.5, z * 0.5)
            
            # Create arrays for batch
            xs = np.array([x * 0.5], dtype=np.float32)
            zs = np.array([z * 0.5], dtype=np.float32)
            vectorized = noise.noise_batch(xs, zs)[0]
            
            np.testing.assert_almost_equal(scalar, vectorized, decimal=5,
                err_msg=f"Mismatch at ({x}, {z})")


def test_grid_matches_scalar():
    """Verify grid output matches individual scalar calls."""
    noise = PerlinNoise2D(seed=12345)
    
    grid = noise.noise_grid(0, 0, 4, 4, 0.25)
    
    for x in range(4):
        for z in range(4):
            scalar = noise.noise(x * 0.25, z * 0.25)
            np.testing.assert_almost_equal(grid[x, z], scalar, decimal=5,
                err_msg=f"Grid mismatch at ({x}, {z})")


def test_convenience_function():
    """Test the get_noise_grid convenience function."""
    grid = get_noise_grid(0, 0, 8, 8, scale=0.1, octaves=2)
    assert grid.shape == (8, 8)
    assert grid.dtype == np.float32
