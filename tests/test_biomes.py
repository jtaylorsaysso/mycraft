"""Tests for biome registry system."""
import pytest
from engine.biomes import Biome, BiomeRegistry, plains_height, forest_height, rocky_height, desert_height, mountain_height, canyon_height


def test_biome_creation():
    """Test creating a biome with required fields."""
    def test_height(x, z):
        return 0
    
    biome = Biome(
        name="test_biome",
        display_name="Test Biome",
        height_function=test_height,
        surface_block="grass",
        subsurface_block="dirt"
    )
    
    assert biome.name == "test_biome"
    assert biome.display_name == "Test Biome"
    assert biome.surface_block == "grass"
    assert biome.subsurface_block == "dirt"
    assert biome.height_function(10, 10) == 0


def test_biome_registry_get_biome():
    """Test retrieving registered biomes."""
    plains = BiomeRegistry.get_biome("plains")
    
    assert plains.name == "plains"
    assert plains.surface_block == "grass"
    assert callable(plains.height_function)


def test_biome_registry_exists():
    """Test checking if a biome is registered."""
    assert BiomeRegistry.exists("plains")
    assert BiomeRegistry.exists("forest")
    assert BiomeRegistry.exists("rocky")
    assert BiomeRegistry.exists("desert")
    assert BiomeRegistry.exists("mountain")
    assert BiomeRegistry.exists("canyon")
    assert not BiomeRegistry.exists("nonexistent_biome")


def test_biome_registry_get_all():
    """Test getting all registered biomes."""
    all_biomes = BiomeRegistry.get_all_biomes()
    
    assert isinstance(all_biomes, dict)
    assert "plains" in all_biomes
    assert "forest" in all_biomes
    assert "rocky" in all_biomes
    assert "desert" in all_biomes
    assert "mountain" in all_biomes
    assert "canyon" in all_biomes


def test_biome_height_functions_are_deterministic():
    """Test that height functions return consistent values."""
    plains = BiomeRegistry.get_biome("plains")
    
    # Same coordinates should return same height
    h1 = plains.height_function(10, 20)
    h2 = plains.height_function(10, 20)
    
    assert h1 == h2
    assert isinstance(h1, int)


def test_different_biomes_different_heights():
    """Test that different biomes produce different terrain."""
    plains_h = plains_height(50, 50)
    rocky_h = rocky_height(50, 50)
    desert_h = desert_height(50, 50)
    
    # At least some biomes should differ at this test point
    heights = [plains_h, rocky_h, desert_h]
    assert len(set(heights)) > 1  # Not all the same


def test_biome_height_functions_return_integers():
    """Test that all biome height functions return integers."""
    test_coords = [(0, 0), (10, 10), (100, 100), (-10, -10)]
    biomes = ["plains", "forest", "rocky", "desert", "mountain", "canyon"]
    
    for biome_name in biomes:
        biome = BiomeRegistry.get_biome(biome_name)
        for x, z in test_coords:
            height = biome.height_function(x, z)
            assert isinstance(height, int), f"{biome_name} at ({x},{z}) returned non-int: {height}"


def test_get_biome_at_returns_valid_biome():
    """Test that get_biome_at returns a registered biome."""
    test_coords = [(0, 0), (100, 100), (-50, 50), (1000, 1000)]
    
    for x, z in test_coords:
        biome = BiomeRegistry.get_biome_at(x, z)
        
        assert biome is not None
        assert biome.name in ["plains", "forest", "rocky", "desert", "mountain", "canyon"]


def test_biome_transitions_are_relatively_smooth():
    """Test that neighboring coordinates don't cause dramatic biome switches."""
    # Sample a 10x10 grid
    biome_changes = 0
    prev_biome = None
    
    for x in range(0, 100, 10):
        for z in range(0, 100, 10):
            biome = BiomeRegistry.get_biome_at(x, z)
            if prev_biome and biome.name != prev_biome.name:
                biome_changes += 1
            prev_biome = biome
    
    # Should have some variety but not change every single coordinate
    assert biome_changes > 0  # At least some variety
    assert biome_changes < 50  # But not chaotic (less than half the samples)


def test_plains_height_range():
    """Test that plains stays within expected range."""
    for x in range(-100, 100, 10):
        for z in range(-100, 100, 10):
            h = plains_height(x, z)
            assert -3 <= h <= 3  # Enhanced range


def test_rocky_height_range():
    """Test that rocky terrain has larger variation."""
    heights = []
    for x in range(-100, 100, 10):
        for z in range(-100, 100, 10):
            h = rocky_height(x, z)
            heights.append(h)
            assert -6 <= h <= 6  # Enhanced range
    
    # Rocky should use most of its range
    assert max(heights) - min(heights) >= 6


def test_desert_height_range():
    """Test that desert is very flat."""
    heights = []
    for x in range(-100, 100, 10):
        for z in range(-100, 100, 10):
            h = desert_height(x, z)
            heights.append(h)
            assert -1 <= h <= 1
    
    # Desert should be relatively flat
    assert max(heights) - min(heights) <= 2


def test_forest_height_matches_plains():
    """Test that forest uses same height function as plains."""
    test_coords = [(0, 0), (50, 50), (100, 100)]
    
    for x, z in test_coords:
        assert forest_height(x, z) == plains_height(x, z)


def test_mountain_height_range():
    """Test that mountain terrain has dramatic variation."""
    heights = []
    for x in range(-100, 100, 10):
        for z in range(-100, 100, 10):
            h = mountain_height(x, z)
            heights.append(h)
            assert -8 <= h <= 12
    
    # Mountain should have significant variation
    assert max(heights) - min(heights) >= 10


def test_canyon_height_range():
    """Test that canyon terrain has deep valleys and low mesas."""
    heights = []
    for x in range(-100, 100, 10):
        for z in range(-100, 100, 10):
            h = canyon_height(x, z)
            heights.append(h)
            assert -6 <= h <= 2
    
    # Canyon should have variety including deep areas
    assert min(heights) <= -2  # Should have some deep valleys
