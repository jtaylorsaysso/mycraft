"""
Example 01: Simple World
A minimal example of setting up a voxel world.
"""
from engine.game import VoxelGame

def main():
    game = VoxelGame(name="Example: Simple World")
    game.spawn_player(position=(0, 15, 0))
    game.run()

if __name__ == "__main__":
    main()
