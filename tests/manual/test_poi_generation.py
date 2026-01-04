"""
Manual verification script for POI generation.
"""

from games.voxel_world.systems.world_gen import VoxelWorldGenerator
from games.voxel_world.pois.shrine_generator import ShrineGenerator
from games.voxel_world.pois.camp_generator import CampGenerator

def test_poi_generation():
    print("Initializing generator...")
    world_gen = VoxelWorldGenerator(seed=123)
    
    # Test Shrine
    print("\nTesting ShrineGenerator:")
    shrine_gen = ShrineGenerator(seed=123)
    
    # Force a position
    valid_pos = shrine_gen.get_spawn_position(
        chunk_x=0, chunk_z=0, chunk_size=16,
        biome_data=None, # Not used yet
        height_callback=world_gen.get_height
    )
    
    if valid_pos:
        print(f"  Valid spawn pos: {valid_pos}")
        poi_data = shrine_gen.generate(valid_pos[0], valid_pos[1], valid_pos[2], seed=123)
        print(f"  Generated {poi_data.poi_type} with {len(poi_data.blocks)} blocks")
        print(f"  Sample blocks: {poi_data.blocks[:3]}")
    else:
        print("  Could not find valid spawn pos (underwater?)")

    # Test Camp
    print("\nTesting CampGenerator:")
    camp_gen = CampGenerator(seed=456)
    
    valid_pos_camp = camp_gen.get_spawn_position(
        chunk_x=5, chunk_z=5, chunk_size=16,
        biome_data=None, 
        height_callback=world_gen.get_height
    )
    
    if valid_pos_camp:
        print(f"  Valid spawn pos: {valid_pos_camp}")
        poi_data = camp_gen.generate(valid_pos_camp[0], valid_pos_camp[1], valid_pos_camp[2], seed=456)
        print(f"  Generated {poi_data.poi_type} with {len(poi_data.blocks)} blocks and {len(poi_data.entities)} entities")
        print(f"  Sample entities: {poi_data.entities}")
    else:
        print("  Could not find valid spawn pos")

if __name__ == "__main__":
    test_poi_generation()
