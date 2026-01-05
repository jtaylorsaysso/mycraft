"""
Voxel World Game Entry Point (Refactored for ECS)
"""
from engine.game import VoxelGame, Block
from engine.ecs.events import Event
from engine.spawn_manager import SpawnManager
from games.voxel_world.biomes.biomes import BiomeRegistry

def run(**kwargs):
    # Extract config
    name = kwargs.get('name', "MyCraft Voxel World")
    hot_config = kwargs.get('hot_config')
    
    # Create game instance
    game = VoxelGame(name=name, config_manager=hot_config)
    
    # Register voxel_world's terrain system (uses engine ChunkManager)
    from games.voxel_world.systems.world_gen import create_terrain_system
    terrain_system = create_terrain_system(
        game.world, 
        game.world.event_bus, 
        game, 
        game.texture_atlas
    )
    game.register_terrain_system(terrain_system)

    
    # Register combat systems
    from games.voxel_world.systems.stamina_system import StaminaSystem
    from games.voxel_world.systems.dodge_system import DodgeSystem
    from games.voxel_world.systems.parry_system import ParrySystem
    from games.voxel_world.systems.combat_system import CombatSystem
    game.world.add_system(StaminaSystem(game.world, game.world.event_bus))
    game.world.add_system(DodgeSystem(game.world, game.world.event_bus))
    game.world.add_system(ParrySystem(game.world, game.world.event_bus))
    game.world.add_system(CombatSystem(game.world, game.world.event_bus))
    
    # Register avatar color system (M2: Avatar Rendering)
    from engine.systems.avatar_color_system import AvatarColorSystem
    game.world.add_system(AvatarColorSystem(game.world, game.world.event_bus, game))

    # Register Health and Loot systems (M3: Combat Loop)
    from games.voxel_world.systems.health_system import HealthSystem
    from games.voxel_world.systems.loot_system import LootSystem
    game.world.add_system(HealthSystem(game.world, game.world.event_bus))
    game.world.add_system(LootSystem(game.world, game.world.event_bus))
    
    # Register Enemy System (M3)
    from games.voxel_world.systems.enemy_system import EnemySystem
    game.world.add_system(EnemySystem(game.world, game.world.event_bus, game))
    
    # Register Projectile System (M5)
    from games.voxel_world.systems.projectile_system import ProjectileSystem
    game.world.add_system(ProjectileSystem(game.world, game.world.event_bus, game))
    
    # Register blocks 
    # (Engine provides defaults in BlockRegistry, we can add game-specific ones here if needed)
    
    # Hook into events
    def on_break(event):
        pass # Logging handled by system
        
    game.world.event_bus.subscribe("on_block_break", on_break)
    
    # Setup game spawn system - handles initialization and player spawning
    from engine.systems.game_spawn import GameSpawnSystem
    spawn_system = GameSpawnSystem(
        game.world,
        game.world.event_bus,
        game,
        terrain_system,
        spawn_delay=1.5,  # Short delay to allow physics to stabilize
        spawn_point=kwargs.get('spawn_point')
    )
    game.world.add_system(spawn_system)
    
    game.run()


if __name__ == "__main__":
    run()
