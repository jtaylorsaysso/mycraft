"""Verification script for Phase 6 Rendering Improvements."""

from engine.game import VoxelGame, Block
import sys

def test_rendering():
    # Force headless-ish or small window for testing if needed
    # But usually we want to see it.
    
    game = VoxelGame(name="Phase 6 Verification")
    
    # Register some blocks
    game.register_block(Block("dirt", (2,0), color="#8B4513"))
    game.register_block(Block("grass", (0,0), color="#228B22"))
    
    # Spawn player
    game.spawn_player(position=(0, 10, 0))
    
    # Run for a few frames then exit (for automated testing)
    # Or just run normally for manual verification.
    if '--auto' in sys.argv:
        def stop_task(task):
            if task.time > 2.0:
                print("Verification successful (2 seconds elapsed)")
                sys.exit(0)
            return task.cont
        game.taskMgr.add(stop_task, "stop_task")
        
    game.run()

if __name__ == "__main__":
    test_rendering()
