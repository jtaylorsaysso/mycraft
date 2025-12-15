
import pytest
from engine.texture_atlas import TextureAtlas
from unittest.mock import MagicMock, patch

@pytest.fixture
def atlas():
    with patch('engine.texture_atlas.load_texture') as mock_load:
        mock_load.return_value = MagicMock()
        return TextureAtlas("mock_path.png")

def test_get_tile_uvs_benchmark(benchmark, atlas):
    """Benchmark calculating UVs for a single tile."""
    benchmark(atlas.get_tile_uvs, 5)

def test_get_tiled_uvs_benchmark(benchmark, atlas):
    """Benchmark calculating UVs for a merged quad (greedy meshing simulation)."""
    # Simulate a 4x4 merged face
    benchmark(atlas.get_tiled_uvs, 5, 4, 4)
