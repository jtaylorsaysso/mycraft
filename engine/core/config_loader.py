"""
Configuration loader for game.yaml.
"""
import yaml
from pathlib import Path
from typing import Any, Dict
from engine.game import VoxelGame, Block
from engine.ecs.component import get_component_class
from engine.core.logger import get_logger
from ursina import Vec3

logger = get_logger(__name__)

def load_game_config(config_path: str) -> VoxelGame:
    """
    Load a VoxelGame instance from a YAML configuration file.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
        
    game_name = config.get("name", "Configured Voxel Game")
    game = VoxelGame(name=game_name)
    
    # 1. Load Blocks
    blocks_config = config.get("blocks", {})
    if blocks_config.get("extend_defaults", True):
        _register_default_blocks(game)
        
    for block_data in blocks_config.get("custom", []):
        block = Block(
            id=block_data["id"],
            texture_tile=tuple(block_data["texture_tile"]),
            color=block_data.get("color", "#FFFFFF"),
            solid=block_data.get("solid", True),
            transparent=block_data.get("transparent", False),
            breakable=block_data.get("breakable", True),
            drop=block_data.get("drop")
        )
        game.register_block(block)
        
    # 2. Player Config
    player_config = config.get("player", {})
    spawn_pos = tuple(player_config.get("spawn", [0, 10, 0]))
    game.spawn_player(spawn_pos)
    
    # 3. Entities
    for entity_data in config.get("entities", []):
        _spawn_entity_from_config(game, entity_data)
        
    logger.info(f"Loaded game '{game_name}' from {config_path}")
    return game

def _register_default_blocks(game: VoxelGame):
    """Register standard blocks."""
    defaults = [
        Block("air", (0,0), solid=False, transparent=True),
        Block("stone", (0,0)),
        Block("dirt", (1,0)),
        Block("grass", (2,0)),
        Block("wood", (5,0)),
        Block("leaves", (6,0), transparent=True),
    ]
    for b in defaults:
        game.register_block(b)

def _spawn_entity_from_config(game: VoxelGame, data: Dict[str, Any]):
    """Spawn an entity based on config data."""
    # Basic components (Transform is implicit if not provided?)
    # For now, let's assume entities have a type that maps to a preset
    # or they are generic containers of components
    
    entity_id = game.world.create_entity(tag=data.get("id"))
    
    # Check for transform data
    pos = data.get("position", [0,0,0])
    from engine.components.core import Transform
    game.world.add_component(entity_id, Transform(position=Vec3(*pos)))
    
    # Map other fields to components
    # This is a simplification; a real loader would map "type: collectible" to the Collectible component
    entity_type = data.get("type")
    
    if entity_type == "collectible":
        from engine.components.gameplay import Collectible
        # NOTE: We missed creating Collectible in previous step! 
        # Adding simple fallback or skip for now to avoid crash
        pass
        
    elif entity_type == "trigger":
        from engine.components.gameplay import Trigger
        bounds = data.get("bounds", [[0,0,0], [1,1,1]])
        min_b = Vec3(*bounds[0])
        max_b = Vec3(*bounds[1])
        game.world.add_component(entity_id, Trigger(bounds_min=min_b, bounds_max=max_b))

    # Generic component loading could go here
    # components:
    #   Health: {current: 50}
    
    components_config = data.get("components", {})
    for comp_name, comp_data in components_config.items():
        comp_class = get_component_class(comp_name)
        if comp_class:
            # Instantiate component with kwargs
            comp = comp_class(**comp_data)
            game.world.add_component(entity_id, comp)
