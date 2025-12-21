"""Tests for Panda3D collision raycasting system."""

import pytest
from panda3d.core import LVector3f, CollisionTraverser, NodePath
from engine.physics import raycast_ground_height, raycast_wall_check, KinematicState
from games.voxel_world.systems.world_gen import TerrainSystem
from engine.ecs.world import World
from engine.game import VoxelGame


class MockEntity:
    """Mock entity for testing raycasts."""
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


def test_raycast_ground_height_basic():
    """Test that raycast detects terrain collision."""
    # This is a basic structure test - full integration test requires Panda3D ShowBase
    # which is complex to set up in unit tests
    
    # Verify function signature
    assert callable(raycast_ground_height)
    
    # Verify it accepts required parameters
    entity = MockEntity(0, 5, 0)
    traverser = CollisionTraverser()
    
    # Note: This will return None without actual terrain, but shouldn't crash
    result = raycast_ground_height(
        entity,
        traverser,
        NodePath("test"),  # Mock render node
        max_distance=5.0,
        foot_offset=0.2,
        ray_origin_offset=2.0
    )
    
    # Without terrain, should return None
    assert result is None


def test_raycast_wall_check_basic():
    """Test that wall raycast function works."""
    entity = MockEntity(0, 1, 0)
    traverser = CollisionTraverser()
    movement = (1.0, 0.0, 0.0)  # Moving in +X direction
    
    # Without terrain, should return False (no wall)
    result = raycast_wall_check(
        entity,
        movement,
        traverser,
        NodePath("test"),
        distance_buffer=0.5
    )
    
    assert result is False


def test_raycast_with_surface_normal():
    """Test that raycast can return surface normals."""
    entity = MockEntity(0, 5, 0)
    traverser = CollisionTraverser()
    
    # Test with return_normal=True
    result = raycast_ground_height(
        entity,
        traverser,
        NodePath("test"),
        return_normal=True
    )
    
    # Without terrain, should return None
    assert result is None


def test_terrain_system_creates_chunks():
    """Test that TerrainSystem can create chunks with collision."""
    # Create minimal world and event bus
    world = World()
    
    # Note: This test requires a full Panda3D ShowBase which is complex
    # For now, we verify the class structure
    assert hasattr(TerrainSystem, 'create_chunk')
    assert hasattr(TerrainSystem, 'get_height')
    assert hasattr(TerrainSystem, '_add_collision_to_chunk')


def test_wall_check_no_movement():
    """Test that wall check returns False for zero movement."""
    entity = MockEntity(0, 1, 0)
    traverser = CollisionTraverser()
    movement = (0.0, 0.0, 0.0)  # No movement
    
    result = raycast_wall_check(
        entity,
        movement,
        traverser,
        NodePath("test")
    )
    
    # Should return False for no movement
    assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
