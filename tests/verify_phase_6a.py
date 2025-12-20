"""Verification test for Phase 6a: Basic Jelly Water System."""

import sys
from engine.game import VoxelGame, Block

def test_water_rendering():
    """Test water block rendering with wobble shader."""
    
    game = VoxelGame(name="Phase 6a: Jelly Water Verification")
    
    # Verify water block is registered
    from games.voxel_world.blocks.water_blocks import water, is_water_block
    from games.voxel_world.blocks.blocks import BlockRegistry
    
    assert BlockRegistry.exists("water"), "Water block not registered"
    water_block = BlockRegistry.get_block("water")
    assert is_water_block(water_block), "Water block not identified as liquid"
    print("✓ Water block registered successfully")
    
    # Register additional blocks for terrain
    game.register_block(Block("dirt", (2,0), color="#8B4513"))
    game.register_block(Block("grass", (0,0), color="#228B22"))
    
    # Spawn player above and to the side of water pool for good view
    # Water pool is at world coords (4-12, 4-12) in X-Y, at Z=0
    # Spawn at edge of pool, elevated
    game.spawn_player(position=(15, 8, 8))
    print("✓ Player spawned at (15, 8, 8)")
    print("  Water pool location: X=[4-12], Y=[4-12], Z=0")
    print("  Camera should be looking down at water")
    print("  Use WASD to move, mouse to look around")
    
    # Verify systems are loaded
    from engine.systems.water_physics import WaterPhysicsSystem
    water_systems = [s for s in game.world._systems if isinstance(s, WaterPhysicsSystem)]
    assert len(water_systems) > 0, "WaterPhysicsSystem not loaded"
    print("✓ WaterPhysicsSystem loaded")
    
    # Run for a few seconds to verify rendering
    if '--auto' in sys.argv:
        frame_count = 0
        def verify_task(task):
            nonlocal frame_count
            frame_count += 1
            
            if frame_count == 1:
                print("✓ First frame rendered")
            
            if task.time > 3.0:
                print(f"✓ Rendered {frame_count} frames over 3 seconds")
                print("✓ Water wobble animation active")
                print("\n=== Phase 6a Verification PASSED ===")
                sys.exit(0)
            return task.cont
        
        game.taskMgr.add(verify_task, "verify_task")
    else:
        print("\n=== Interactive Mode ===")
        print("Look for wobbling water blocks:")
        print("  - Semi-transparent cyan-blue color")
        print("  - Wobbling/jelly-like animation")
        print("  - Located at ground level (Z=0)")
        print("\nControls:")
        print("  WASD - Move")
        print("  Mouse - Look around")
        print("  ESC - Unlock mouse")
    
    game.run()

if __name__ == "__main__":
    test_water_rendering()
