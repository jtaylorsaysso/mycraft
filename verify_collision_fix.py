#!/usr/bin/env python3
"""Verification script for side face collision with varied terrain."""

from games.voxel_world.systems.world_gen import TerrainSystem
from games.voxel_world.biomes.biomes import BiomeRegistry
from panda3d.core import CollisionNode, NodePath
from unittest.mock import Mock

def test_collision_at_chunk(chunk_x, chunk_z):
    """Test collision generation at a specific chunk."""
    
    # Create mock base with render
    mock_base = Mock()
    mock_render = Mock()
    mock_base.render = mock_render
    
    # Track collision nodes
    collision_nodes = []
    
    def mock_attach(node):
        if isinstance(node, CollisionNode):
            collision_nodes.append(node)
        np = Mock(spec=NodePath)
        np.attachNewNode = mock_attach
        np.setTexture = Mock()
        return np
    
    mock_render.attachNewNode = mock_attach
    
    # Create terrain system
    terrain = TerrainSystem(
        world=Mock(),
        event_bus=Mock(),
        base=mock_base,
        texture_atlas=None
    )
    
    # Create chunk
    chunk_np = terrain.create_chunk(chunk_x, chunk_z)
    
    # Get collision node
    if not collision_nodes:
        return 0, 0
    
    cnode = collision_nodes[0]
    num_solids = cnode.getNumSolids()
    
    # Calculate expected top faces (16x16 * 2 triangles)
    expected_top = 16 * 16 * 2
    side_faces = max(0, num_solids - expected_top)
    
    return num_solids, side_faces

def main():
    print("Testing collision generation across multiple chunks...\n")
    
    # Test several chunks to find terrain variation
    test_chunks = [
        (0, 0),
        (1, 1),
        (5, 5),
        (10, 10),
        (-5, -5),
    ]
    
    total_side_faces = 0
    
    for cx, cz in test_chunks:
        num_solids, side_faces = test_collision_at_chunk(cx, cz)
        print(f"Chunk ({cx:3}, {cz:3}): {num_solids:5} total solids, {side_faces:5} side face solids")
        total_side_faces += side_faces
    
    print(f"\n{'='*60}")
    if total_side_faces > 0:
        print(f"✅ SUCCESS: Side face collision detected!")
        print(f"   Total side face solids across all test chunks: {total_side_faces}")
        print(f"\n   Side faces are being generated where terrain has height differences.")
        return True
    else:
        print(f"⚠️  WARNING: No side faces detected in any test chunk")
        print(f"   This could mean:")
        print(f"   1. Terrain is completely flat (unlikely across 5 chunks)")
        print(f"   2. Side face generation logic may need debugging")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
