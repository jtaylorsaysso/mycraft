"""Tests for block registry system."""
import pytest
from engine.blocks import Block, BlockRegistry


def test_block_creation():
    """Test creating a block with required fields."""
    block = Block(
        name="test_block",
        color=(0.5, 0.5, 0.5),
        tile_top=0,
        tile_side=1,
        tile_bottom=2
    )
    
    assert block.name == "test_block"
    assert block.color == (0.5, 0.5, 0.5)
    assert block.tile_top == 0
    assert block.tile_side == 1
    assert block.tile_bottom == 2
    assert block.display_name == "Test_block"  # Auto-generated


def test_block_display_name_override():
    """Test that display_name can be manually set."""
    block = Block(
        name="stone",
        color=(0.5, 0.5, 0.5),
        display_name="Cool Stone"
    )
    
    assert block.display_name == "Cool Stone"


def test_block_get_face_tile():
    """Test getting tile indices for different faces."""
    block = Block(
        name="test_block",
        color=(0.5, 0.5, 0.5),
        tile_top=10,
        tile_side=20,
        tile_bottom=30
    )
    
    assert block.get_face_tile('top') == 10
    assert block.get_face_tile('side') == 20
    assert block.get_face_tile('bottom') == 30


def test_block_get_face_tile_invalid():
    """Test that invalid face names raise errors."""
    block = Block(
        name="test_block",
        color=(0.5, 0.5, 0.5),
        tile_top=0
    )
    
    with pytest.raises(ValueError):
        block.get_face_tile('invalid_face')


def test_block_registry_get_block():
    """Test retrieving registered blocks."""
    # Predefined blocks should exist
    grass = BlockRegistry.get_block("grass")
    
    assert grass.name == "grass"
    assert isinstance(grass.color, tuple)
    assert len(grass.color) == 3


def test_block_registry_exists():
    """Test checking if a block is registered."""
    assert BlockRegistry.exists("grass")
    assert BlockRegistry.exists("dirt")
    assert BlockRegistry.exists("stone")
    assert not BlockRegistry.exists("nonexistent_block")


def test_block_registry_get_all():
    """Test getting all registered blocks."""
    all_blocks = BlockRegistry.get_all_blocks()
    
    assert isinstance(all_blocks, dict)
    assert "grass" in all_blocks
    assert "dirt" in all_blocks
    assert "stone" in all_blocks
    assert "sand" in all_blocks


def test_predefined_blocks_have_colors():
    """Test that all predefined blocks have valid colors."""
    predefined = [
        "grass", "dirt", "stone", "sand", "gravel", "snow", "clay", "wood",
        "cobblestone_mossy", "podzol", "sandstone", "ice", "stone_mossy",
        "red_sand", "terracotta", "red_sandstone", "andesite", "granite"
    ]
    
    for block_name in predefined:
        block = BlockRegistry.get_block(block_name)
        
        # Color should be RGB tuple with values 0-1
        assert isinstance(block.color, tuple)
        assert len(block.color) == 3
        
        for component in block.color:
            assert 0.0 <= component <= 1.0


def test_predefined_blocks_have_tiles():
    """Test that all predefined blocks have valid tile indices."""
    predefined = [
        "grass", "dirt", "stone", "sand", "gravel", "snow", "clay", "wood",
        "cobblestone_mossy", "podzol", "sandstone", "ice", "stone_mossy",
        "red_sand", "terracotta", "red_sandstone", "andesite", "granite"
    ]
    
    for block_name in predefined:
        block = BlockRegistry.get_block(block_name)
        
        # All blocks should have at least top and side tiles
        assert block.tile_top is not None, f"{block_name} missing tile_top"
        assert block.tile_side is not None, f"{block_name} missing tile_side"
        
        # Tile indices should be in valid range (0-255)
        assert 0 <= block.tile_top <= 255
        assert 0 <= block.tile_side <= 255
        
        if block.tile_bottom is not None:
            assert 0 <= block.tile_bottom <= 255


def test_block_registry_missing_block_raises_error():
    """Test that accessing non-existent block raises KeyError."""
    with pytest.raises(KeyError):
        BlockRegistry.get_block("this_block_does_not_exist")


def test_block_colors_are_distinct():
    """Test that different block types have different colors for visual distinction."""
    grass = BlockRegistry.get_block("grass")
    dirt = BlockRegistry.get_block("dirt")
    stone = BlockRegistry.get_block("stone")
    sand = BlockRegistry.get_block("sand")
    
    # All should have different colors
    assert grass.color != dirt.color
    assert grass.color != stone.color
    assert grass.color != sand.color
    assert dirt.color != stone.color


def test_grass_block_has_different_top_and_side():
    """Test that grass block has different textures for top and side (Minecraft-style)."""
    grass = BlockRegistry.get_block("grass")
    
    # Grass should have different top and side tiles
    assert grass.tile_top != grass.tile_side
    assert grass.tile_top == 0  # Grass top
    assert grass.tile_side == 3  # Grass side
    assert grass.tile_bottom == 2  # Dirt
