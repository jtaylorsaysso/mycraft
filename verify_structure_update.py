
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), ".")))

try:
    from games.voxel_world.blocks.blocks import BlockRegistry
    from games.voxel_world.systems.world_gen import TerrainSystem
    from games.voxel_world.structures.vegetation_generator import VegetationGenerator
    from games.voxel_world.structures.desert_generator import CactusGenerator
    
    print("Imports successful.")
    
    # Check Blocks
    required_blocks = ["water", "cactus", "dead_bush", "tall_grass", "flower", "fern", "mushroom"]
    for b in required_blocks:
        if not BlockRegistry.exists(b):
            print(f"FAIL: Block '{b}' missing!")
            sys.exit(1)
        blk = BlockRegistry.get_block(b)
        print(f"Block '{b}': solid={blk.solid}, transparent={blk.transparent}")
        
    print("All blocks verified.")
    
    # Check Generator instantiation
    veg = VegetationGenerator(seed=123)
    cactus = CactusGenerator(seed=123)
    print("Generators instantiated.")
    
    print("SUCCESS")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
