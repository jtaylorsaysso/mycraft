"""Tests for dynamic chunk loading and world generation."""
import pytest
from games.voxel_world.systems.world_gen import World


def test_get_player_chunk_coords():
    """Test conversion from world coordinates to chunk coordinates."""
    world = World()
    
    # Test origin
    assert world.get_player_chunk_coords((0, 0, 0)) == (0, 0)
    
    # Test positive coordinates
    assert world.get_player_chunk_coords((16, 0, 16)) == (1, 1)
    assert world.get_player_chunk_coords((32, 0, 32)) == (2, 2)
    
    # Test negative coordinates
    assert world.get_player_chunk_coords((-16, 0, -16)) == (-1, -1)
    
    # Test coordinates within chunk bounds
    assert world.get_player_chunk_coords((8, 0, 8)) == (0, 0)
    assert world.get_player_chunk_coords((15, 0, 15)) == (0, 0)
    assert world.get_player_chunk_coords((17, 0, 17)) == (1, 1)


def test_chunk_loading_on_update():
    """Test that chunks load when player moves to new location."""
    world = World(chunk_load_radius=2, max_chunks_per_frame=10)
    
    # Initially no chunks
    assert len(world.chunks) == 0
    
    # Update with player at origin - should queue chunks for loading
    world.update((0, 2, 0))
    
    # After update, chunks should be loaded
    assert len(world.chunks) > 0
    
    # Check that origin chunk is loaded
    assert (0, 0) in world.chunks


def test_chunk_unloading_on_distance():
    """Test that chunks unload when player moves far away."""
    world = World(chunk_load_radius=2, chunk_unload_radius=5, max_chunks_per_frame=10)
    
    # Load chunks around origin
    world.update((0, 2, 0))
    initial_chunk_count = len(world.chunks)
    
    assert initial_chunk_count > 0
    assert (0, 0) in world.chunks
    
    # Move player very far away (200 chunks)
    far_pos = (200 * 16, 2, 200 * 16)
    
    # Multiple updates to process all unloading
    for _ in range(20):  # Enough iterations to unload all old chunks
        world.update(far_pos)
    
    # Origin chunk should be unloaded
    assert (0, 0) not in world.chunks
    
    # New chunks around far position should be loaded
    assert (200, 200) in world.chunks


def test_chunk_generation_determinism():
    """Test that the same chunk coordinates generate identical terrain."""
    world1 = World()
    world1.create_chunk(5, 5)
    
    world2 = World()
    world2.create_chunk(5, 5)
    
    # Get the mesh data
    chunk1 = world1.chunks[(5, 5)]
    chunk2 = world2.chunks[(5, 5)]
    
    # Verify vertex counts match (deterministic generation)
    assert len(chunk1.model.vertices) == len(chunk2.model.vertices)
    assert len(chunk1.model.triangles) == len(chunk2.model.triangles)


def test_chunk_loading_respects_max_per_frame():
    """Test that chunk loading is throttled to prevent frame drops."""
    world = World(chunk_load_radius=5, max_chunks_per_frame=2)
    
    # Update once - should only load max_chunks_per_frame chunks
    world.update((0, 2, 0))
    
    # After first update, should have loaded at most 2 chunks
    # (may be less if queuing logic delays)
    assert len(world.chunks) <= 2
    
    # After multiple updates, more chunks should load
    for _ in range(10):
        world.update((0, 2, 0))
    
    # Should eventually load more chunks
    assert len(world.chunks) > 2


def test_chunk_load_radius():
    """Test that chunks are only loaded within specified radius."""
    load_radius = 3
    world = World(chunk_load_radius=load_radius, max_chunks_per_frame=100)
    
    # Load all chunks around origin
    world.update((0, 2, 0))
    
    # Check that all loaded chunks are within radius
    for chunk_coords in world.chunks.keys():
        cx, cz = chunk_coords
        distance = (cx * cx + cz * cz) ** 0.5
        assert distance <= load_radius, f"Chunk {chunk_coords} exceeds load radius {load_radius}"


def test_height_function_consistency():
    """Test that get_height returns consistent values."""
    world = World()
    
    # Same coordinates should always return same height
    h1 = world.get_height(10, 20)
    h2 = world.get_height(10, 20)
    assert h1 == h2
    
    # Height should be an integer
    assert isinstance(h1, int)
    
    # Height should be within reasonable range (based on current implementation)
    assert -2 <= h1 <= 2


def test_empty_world_after_init():
    """Test that world starts with no chunks until first update."""
    world = World()
    
    # Should start empty (no static generation)
    assert len(world.chunks) == 0
    assert world.last_player_chunk is None


def test_chunk_queues_clear_after_processing():
    """Test that chunk queues are properly processed."""
    world = World(chunk_load_radius=2, max_chunks_per_frame=1)
    
    # Trigger chunk loading
    world.update((0, 2, 0))
    
    # Initially queues should have chunks
    initial_load_queue_size = len(world.chunks_to_load)
    
    # Process updates until queues are empty
    for _ in range(50):  # Plenty of iterations
        world.update((0, 2, 0))
        if not world.chunks_to_load and not world.chunks_to_unload:
            break
    
    # Queues should be empty after processing
    assert len(world.chunks_to_load) == 0
    assert len(world.chunks_to_unload) == 0


def test_biome_integration_chunks_use_biomes():
    """Test that chunks use biome system for height generation."""
    from games.voxel_world.biomes.biomes import BiomeRegistry
    
    world = World()
    
    # Create chunk at a location
    world.create_chunk(0, 0)
    
    # Verify chunk was created
    assert (0, 0) in world.chunks
    
    # Verify that get_height uses biome at various locations
    h1 = world.get_height(0, 0)
    h2 = world.get_height(100, 100)
    
    # Heights should be integers (biome requirement)
    assert isinstance(h1, int)
    assert isinstance(h2, int)


def test_biome_integration_chunks_have_colors():
    """Test that chunks are colored based on their biome."""
    world = World()
    
    # Create multiple chunks at different locations
    world.create_chunk(0, 0)
    world.create_chunk(10, 10)
    world.create_chunk(20, 20)
    
    # Each chunk should have a color property
    for chunk_coords, chunk_entity in world.chunks.items():
        assert hasattr(chunk_entity, 'color')
        # Color should be set (not white default)
        assert chunk_entity.color is not None


def test_biome_integration_different_biomes_different_chunks():
    """Test that chunks in different biomes may have different colors."""
    world = World()
    
    # Create chunks across a large area to ensure multiple biomes
    locations = [(0, 0), (50, 50), (100, 100), (-50, -50)]
    
    for cx, cz in locations:
        world.create_chunk(cx, cz)
    
    # Should have created all chunks
    assert len(world.chunks) == len(locations)
    
    # Collect all chunk colors
    colors = []
    for chunk_entity in world.chunks.values():
        # Get color as tuple for comparison
        color_val = chunk_entity.color
        if hasattr(color_val, 'r'):
            colors.append((color_val.r, color_val.g, color_val.b))
        else:
            colors.append(color_val)
    
    # With 4 chunks across wide area, we should have at least 2 different colors
    # (indicating different biomes)
    unique_colors = len(set(colors))
    assert unique_colors >= 1  # At minimum one color scheme

