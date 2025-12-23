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
    
    # Create game instance
    game = VoxelGame(name=name)
    
    # Register voxel_world's terrain system
    from games.voxel_world.systems.world_gen import TerrainSystem
    terrain_system = TerrainSystem(
        game.world, 
        game.world.event_bus, 
        game, 
        game.texture_atlas
    )
    game.register_terrain_system(terrain_system)
    
    # Register blocks 
    # (Engine provides defaults in BlockRegistry, we can add game-specific ones here if needed)
    
    # Hook into events
    def on_break(event):
        pass # Logging handled by system
        
    game.world.event_bus.subscribe("on_block_break", on_break)
    
    # STEP 1: Generate initial chunks FIRST (before spawning player)
    # Terrain system was registered above, retrieve it for chunk generation
    if terrain_system:
        print("🌍 Generating initial chunks...")
        # Create 3x3 grid of chunks centered at origin
        for cx in range(-1, 2):
            for cz in range(-1, 2):
                terrain_system.create_chunk(cx, cz)
                print(f"  ✓ Chunk ({cx}, {cz}) created")
        print("✅ Generated 9 chunks around spawn")
    else:
        print("❌ WARNING: TerrainSystem not found!")
    
    # STEP 2: Initialize SpawnManager for cooperative multiplayer
    spawn_manager = SpawnManager(world_spawn=(0, 0, 10))
    
    # Get existing players (for late-join spawning)
    existing_players = []
    for entity_id in game.world.get_entities_with():
        if game.world.get_entity_by_tag("player") and entity_id != game.world.get_entity_by_tag("player"):
            from engine.components.core import Transform
            transform = game.world.get_component(entity_id, Transform)
            if transform:
                existing_players.append(transform.position)
    
    # STEP 3: Calculate spawn position using SpawnManager
    spawn_pos = kwargs.get('spawn_point')
    
    if not spawn_pos:
        print("🎯 Calculating spawn position...")
        # Use SpawnManager with cooperative player proximity
        spawn_pos = spawn_manager.find_spawn_position(
            terrain_system=terrain_system,
            existing_players=existing_players if existing_players else None,
            biome_registry=BiomeRegistry
        )
        print(f"✅ Calculated spawn position: {spawn_pos}")
    else:
        print(f"📍 Using override spawn position: {spawn_pos}")

    # STEP 4: Delayed player spawn (5 second buffer for terrain loading)
    print(f"⏳ Waiting 5 seconds for terrain to fully load...")
    
    def delayed_spawn(task):
        """Spawn player after delay."""
        print(f"👤 Spawning player at {spawn_pos}...")
        game.spawn_player(position=spawn_pos)
        print("✅ Player spawned")
        
        # STEP 5: Grant spawn protection
        player_id = game.world.get_entity_by_tag("player")
        if player_id:
            # Add spawn protection component
            from engine.components.core import Health
            health = game.world.get_component(player_id, Health)
            if health:
                health.invulnerable = True
                health.invuln_timer = 3.0  # 3 second protection
                print(f"🛡️ Spawn protection active for 3 seconds")
        
        return task.done  # Task completes after running once
    
    # Schedule delayed spawn (5 seconds from now)
    game.taskMgr.doMethodLater(5.0, delayed_spawn, 'delayed_player_spawn')
    
    game.run()


if __name__ == "__main__":
    run()
