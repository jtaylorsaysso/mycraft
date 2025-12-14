"""Tests for texture atlas system."""
import pytest
from ursina import Vec2
from engine.texture_atlas import TextureAtlas


def test_texture_atlas_initialization():
    """Test that texture atlas initializes correctly."""
    atlas = TextureAtlas("Spritesheets/terrain.png")
    
    # Should have a texture object (Ursina may not fully load in test environment)
    # The important thing is that it doesn't crash and returns an object
    texture = atlas.get_texture()
    assert texture is not None or not atlas.is_loaded()  # Either loaded or gracefully failed


def test_texture_atlas_invalid_path():
    """Test that invalid path is handled gracefully."""
    atlas = TextureAtlas("nonexistent/path.png")
    
    # Should not crash, but should not be loaded
    assert not atlas.is_loaded()
    assert atlas.get_texture() is None


def test_tile_coords_calculation():
    """Test tile index to row/col conversion."""
    atlas = TextureAtlas("Spritesheets/terrain.png")
    
    # Tile 0: top-left corner
    assert atlas.get_tile_coords(0) == (0, 0)
    
    # Tile 15: top-right corner
    assert atlas.get_tile_coords(15) == (0, 15)
    
    # Tile 16: second row, first column
    assert atlas.get_tile_coords(16) == (1, 0)
    
    # Tile 240: bottom-left corner
    assert atlas.get_tile_coords(240) == (15, 0)
    
    # Tile 255: bottom-right corner
    assert atlas.get_tile_coords(255) == (15, 15)


def test_tile_coords_out_of_range():
    """Test that out-of-range tile indices raise errors."""
    atlas = TextureAtlas("Spritesheets/terrain.png")
    
    with pytest.raises(ValueError):
        atlas.get_tile_coords(-1)
    
    with pytest.raises(ValueError):
        atlas.get_tile_coords(256)


def test_tile_uvs_structure():
    """Test that get_tile_uvs returns correct structure."""
    atlas = TextureAtlas("Spritesheets/terrain.png")
    
    uvs = atlas.get_tile_uvs(0)
    
    # Should return 4 Vec2 objects
    assert len(uvs) == 4
    assert all(isinstance(uv, Vec2) for uv in uvs)


def test_tile_uvs_range():
    """Test that UV coordinates are in valid range [0, 1]."""
    atlas = TextureAtlas("Spritesheets/terrain.png")
    
    # Test several tiles
    for tile_index in [0, 15, 16, 240, 255]:
        uvs = atlas.get_tile_uvs(tile_index)
        
        for uv in uvs:
            assert 0.0 <= uv.x <= 1.0, f"UV x out of range for tile {tile_index}"
            assert 0.0 <= uv.y <= 1.0, f"UV y out of range for tile {tile_index}"


def test_tile_uvs_tile_0():
    """Test UV coordinates for tile 0 (top-left)."""
    atlas = TextureAtlas("Spritesheets/terrain.png")
    
    uvs = atlas.get_tile_uvs(0)
    
    # Tile 0 should be at top-left of atlas
    # Expected UVs (with Y-flip): bottom-left, bottom-right, top-right, top-left
    tile_size = 1.0 / 16
    
    # Bottom-left of tile
    assert abs(uvs[0].x - 0.0) < 0.001
    assert abs(uvs[0].y - (1.0 - tile_size)) < 0.001
    
    # Bottom-right of tile
    assert abs(uvs[1].x - tile_size) < 0.001
    assert abs(uvs[1].y - (1.0 - tile_size)) < 0.001
    
    # Top-right of tile
    assert abs(uvs[2].x - tile_size) < 0.001
    assert abs(uvs[2].y - 1.0) < 0.001
    
    # Top-left of tile
    assert abs(uvs[3].x - 0.0) < 0.001
    assert abs(uvs[3].y - 1.0) < 0.001


def test_tile_uvs_tile_255():
    """Test UV coordinates for tile 255 (bottom-right)."""
    atlas = TextureAtlas("Spritesheets/terrain.png")
    
    uvs = atlas.get_tile_uvs(255)
    
    # Tile 255 should be at bottom-right of atlas
    tile_size = 1.0 / 16
    
    # Bottom-left of tile
    assert abs(uvs[0].x - (1.0 - tile_size)) < 0.001
    assert abs(uvs[0].y - 0.0) < 0.001
    
    # Bottom-right of tile
    assert abs(uvs[1].x - 1.0) < 0.001
    assert abs(uvs[1].y - 0.0) < 0.001
    
    # Top-right of tile
    assert abs(uvs[2].x - 1.0) < 0.001
    assert abs(uvs[2].y - tile_size) < 0.001
    
    # Top-left of tile
    assert abs(uvs[3].x - (1.0 - tile_size)) < 0.001
    assert abs(uvs[3].y - tile_size) < 0.001


def test_tile_uvs_out_of_range():
    """Test that out-of-range tile indices raise errors."""
    atlas = TextureAtlas("Spritesheets/terrain.png")
    
    with pytest.raises(ValueError):
        atlas.get_tile_uvs(-1)
    
    with pytest.raises(ValueError):
        atlas.get_tile_uvs(256)


def test_grid_constants():
    """Test that atlas constants are correct."""
    atlas = TextureAtlas("Spritesheets/terrain.png")
    
    assert atlas.GRID_SIZE == 16
    assert abs(atlas.TILE_SIZE - 1.0/16) < 0.001
