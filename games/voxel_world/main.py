"""
Voxel World Game Entry Point (Refactored for ECS)
"""
from engine.game import VoxelGame, Block
from engine.ecs.events import Event

def main():
    # Option 2: Config-based (Recommended for beginners)
    # game = VoxelGame.from_config("games/voxel_world/game.yaml")
    
    # Option 1: Code-based (For flexibility)
    game = VoxelGame(name="MyCraft Voxel World")
    
    # Register blocks (Engine provides defaults, we can add more)
    game.register_block(Block("gold_ore", (3,0), color="#FFD700", breakable=True))
    
    # Hook into events
    @game.world.event_bus.subscribe("on_block_break")
    def on_break(event):
        print(f"Block broken: {event.block_type}")
        
    game.spawn_player(position=(0, 10, 0))
    
    game.run()

if __name__ == "__main__":
    main()
