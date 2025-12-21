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
    
    # Register blocks (Engine provides defaults, we can add more)
    game.register_block(Block("gold_ore", (3,0), color="#FFD700", breakable=True))
    
    # Register Game-Specific Systems
    from games.voxel_world.systems.gameplay_input import GameplayInputSystem
    game.world.add_system(GameplayInputSystem(game.world, game.world.event_bus, game))
    
    # Hook into events
    def on_break(event):
        print(f"Block broken: {event.block_type}")
        
    game.world.event_bus.subscribe("on_block_break", on_break)
        
    game.spawn_player(position=(0, 10, 0))
    
    game.run()

if __name__ == "__main__":
    run()
