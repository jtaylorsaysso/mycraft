"""
Voxel World Game Entry Point (Refactored for ECS)
"""
from engine.game import VoxelGame, Block
from engine.ecs.events import Event

def run(**kwargs):
    # Extract config
    name = kwargs.get('name', "MyCraft Voxel World")
    
    # Option 1: Code-based (For flexibility)
    game = VoxelGame(name=name)
    
    # Register blocks 
    # (Engine provides defaults in BlockRegistry, we can add game-specific ones here if needed)
    
    # Hook into events
    def on_break(event):
        pass # Logging handled by system
        
    game.world.event_bus.subscribe("on_block_break", on_break)
        
    # Use configured spawn or default to surface
    spawn_pos = kwargs.get('spawn_point')
    
    if not spawn_pos:
        # Dynamic spawn: Find ground height at (0,0)
        terrain_system = game.world.get_system_by_type("TerrainSystem")
        if terrain_system:
            y = terrain_system.get_height(0, 0)
            spawn_pos = (0, y + 2.0, 0) # +2 safety buffer
        else:
            spawn_pos = (0, 10, 0) # Fallback

    game.spawn_player(position=spawn_pos)
    
    # Generate initial chunks around spawn
    terrain_system = game.world.get_system_by_type("TerrainSystem")
    if terrain_system:
        # Create 3x3 grid of chunks centered at origin
        for cx in range(-1, 2):
            for cz in range(-1, 2):
                terrain_system.create_chunk(cx, cz)
        print("Generated 9 chunks around spawn")
    
    game.run()

if __name__ == "__main__":
    run()
