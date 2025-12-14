"""Block type definitions and registry.

This module defines the core block types used in world generation.
Each block has a color (for immediate rendering) and an optional texture name
(stubbed for future texture implementation).

The colored block approach allows rapid prototyping and performance baselining
without texture asset management overhead.
"""

from dataclasses import dataclass
from typing import Optional, Dict


from engine.texture_atlas import TileRegistry

@dataclass
class Block:
    """Represents a single block type.
    
    Attributes:
        name: Internal identifier (lowercase, no spaces)
        color: RGB tuple (0.0-1.0 range) for colored rendering (fallback)
        tile_top: Tile index (0-255) in terrain.png for top face
        tile_side: Tile index (0-255) in terrain.png for side faces
        tile_bottom: Tile index (0-255) in terrain.png for bottom face
        display_name: Human-readable name for UI/debugging
    """
    name: str
    color: tuple[float, float, float]
    tile_top: Optional[int] = None
    tile_side: Optional[int] = None
    tile_bottom: Optional[int] = None
    display_name: str = ""
    
    def __post_init__(self):
        """Set display_name from name if not provided."""
        if not self.display_name:
            self.display_name = self.name.capitalize()
    
    def get_face_tile(self, face: str) -> Optional[int]:
        """Get tile index for a specific face.
        
        Args:
            face: Face identifier ('top', 'side', or 'bottom')
            
        Returns:
            Tile index (0-255) or None if not set
            
        Raises:
            ValueError: If face is not recognized
        """
        if face == 'top':
            return self.tile_top
        elif face == 'side':
            return self.tile_side
        elif face == 'bottom':
            return self.tile_bottom
        else:
            raise ValueError(f"Unknown face type: {face}. Must be 'top', 'side', or 'bottom'")



class BlockRegistry:
    """Central registry for all block types.
    
    Singleton pattern - use BlockRegistry.register() and BlockRegistry.get_block()
    """
    
    _blocks: Dict[str, Block] = {}
    
    @classmethod
    def register(cls, block: Block) -> None:
        """Register a new block type.
        
        Args:
            block: Block instance to register
            
        Raises:
            ValueError: If block name already registered
        """
        if block.name in cls._blocks:
            raise ValueError(f"Block '{block.name}' already registered")
        cls._blocks[block.name] = block
    
    @classmethod
    def get_block(cls, name: str) -> Block:
        """Look up a block by name.
        
        Args:
            name: Block identifier
            
        Returns:
            Block instance
            
        Raises:
            KeyError: If block not found
        """
        if name not in cls._blocks:
            raise KeyError(f"Block '{name}' not registered")
        return cls._blocks[name]
    
    @classmethod
    def exists(cls, name: str) -> bool:
        """Check if a block is registered.
        
        Args:
            name: Block identifier
            
        Returns:
            True if block exists in registry
        """
        return name in cls._blocks
    
    @classmethod
    def get_all_blocks(cls) -> Dict[str, Block]:
        """Get all registered blocks.
        
        Returns:
            Dictionary of block name -> Block instance
        """
        return cls._blocks.copy()


# Register default block types
# Colors chosen for visual distinction and biome identification
# Tile indices from terrain.png (classic Minecraft 16x16 atlas)

BlockRegistry.register(Block(
    name="grass",
    color=(0.4, 0.7, 0.3),  # Vibrant green (fallback)
    tile_top=TileRegistry.GRASS_TOP,
    tile_side=TileRegistry.GRASS_SIDE,
    tile_bottom=TileRegistry.DIRT,
    display_name="Grass"
))

BlockRegistry.register(Block(
    name="dirt",
    color=(0.5, 0.35, 0.2),  # Rich brown (fallback)
    tile_top=TileRegistry.DIRT,
    tile_side=TileRegistry.DIRT,
    tile_bottom=TileRegistry.DIRT,
    display_name="Dirt"
))

BlockRegistry.register(Block(
    name="stone",
    color=(0.5, 0.5, 0.5),  # Medium grey (fallback)
    tile_top=TileRegistry.STONE,
    tile_side=TileRegistry.STONE,
    tile_bottom=TileRegistry.STONE,
    display_name="Stone"
))

BlockRegistry.register(Block(
    name="sand",
    color=(0.9, 0.8, 0.5),  # Warm yellow (fallback)
    tile_top=TileRegistry.SAND,
    tile_side=TileRegistry.SAND,
    tile_bottom=TileRegistry.SAND,
    display_name="Sand"
))

BlockRegistry.register(Block(
    name="gravel",
    color=(0.4, 0.4, 0.4),  # Dark grey (fallback)
    tile_top=TileRegistry.GRAVEL,
    tile_side=TileRegistry.GRAVEL,
    tile_bottom=TileRegistry.GRAVEL,
    display_name="Gravel"
))

BlockRegistry.register(Block(
    name="snow",
    color=(0.95, 0.95, 0.98),  # Pure white with slight blue tint (fallback)
    tile_top=TileRegistry.SNOW,
    tile_side=TileRegistry.SNOW_SIDE,
    tile_bottom=TileRegistry.DIRT,
    display_name="Snow"
))

BlockRegistry.register(Block(
    name="clay",
    color=(0.7, 0.6, 0.5),  # Tan/beige (fallback)
    tile_top=TileRegistry.CLAY,
    tile_side=TileRegistry.CLAY,
    tile_bottom=TileRegistry.CLAY,
    display_name="Clay"
))

BlockRegistry.register(Block(
    name="wood",
    color=(0.35, 0.25, 0.15),  # Dark brown (fallback)
    tile_top=TileRegistry.LOG_TOP,
    tile_side=TileRegistry.LOG_SIDE,
    tile_bottom=TileRegistry.LOG_TOP,
    display_name="Wood"
))

# Natural terrain variations for diverse biomes
BlockRegistry.register(Block(
    name="cobblestone_mossy",
    color=(0.45, 0.55, 0.4),  # Greenish grey (fallback)
    tile_top=TileRegistry.COBBLESTONE_MOSSY,
    tile_side=TileRegistry.COBBLESTONE_MOSSY,
    tile_bottom=TileRegistry.COBBLESTONE_MOSSY,
    display_name="Mossy Cobblestone"
))

BlockRegistry.register(Block(
    name="podzol",
    color=(0.4, 0.3, 0.2),  # Dark brown (fallback)
    tile_top=TileRegistry.DIRT_PODZOL,
    tile_side=TileRegistry.DIRT_PODZOL,
    tile_bottom=TileRegistry.DIRT,
    display_name="Podzol"
))

BlockRegistry.register(Block(
    name="sandstone",
    color=(0.85, 0.75, 0.5),  # Sandy beige (fallback)
    tile_top=TileRegistry.SANDSTONE,
    tile_side=TileRegistry.SANDSTONE,
    tile_bottom=TileRegistry.SANDSTONE,
    display_name="Sandstone"
))

# Mountain/snow terrain
BlockRegistry.register(Block(
    name="ice",
    color=(0.7, 0.85, 0.95),  # Light blue (fallback)
    tile_top=TileRegistry.ICE_PACKED,
    tile_side=TileRegistry.ICE_PACKED,
    tile_bottom=TileRegistry.ICE_PACKED,
    display_name="Ice"
))

BlockRegistry.register(Block(
    name="stone_mossy",
    color=(0.5, 0.6, 0.5),  # Mossy grey (fallback)
    tile_top=TileRegistry.STONE_MOSSY,
    tile_side=TileRegistry.STONE_MOSSY,
    tile_bottom=TileRegistry.STONE_MOSSY,
    display_name="Mossy Stone"
))

# Canyon/mesa terrain
BlockRegistry.register(Block(
    name="red_sand",
    color=(0.75, 0.4, 0.25),  # Reddish orange (fallback)
    tile_top=TileRegistry.RED_SAND,
    tile_side=TileRegistry.RED_SAND,
    tile_bottom=TileRegistry.RED_SAND,
    display_name="Red Sand"
))

BlockRegistry.register(Block(
    name="terracotta",
    color=(0.65, 0.45, 0.35),  # Clay red (fallback)
    tile_top=TileRegistry.CLAY_TERRACOTTA,
    tile_side=TileRegistry.CLAY_TERRACOTTA,
    tile_bottom=TileRegistry.CLAY_TERRACOTTA,
    display_name="Terracotta"
))

BlockRegistry.register(Block(
    name="red_sandstone",
    color=(0.7, 0.4, 0.3),  # Red-tan (fallback)
    tile_top=TileRegistry.RED_SANDSTONE,
    tile_side=TileRegistry.RED_SANDSTONE,
    tile_bottom=TileRegistry.RED_SANDSTONE,
    display_name="Red Sandstone"
))

# Rock variations for visual interest
BlockRegistry.register(Block(
    name="andesite",
    color=(0.55, 0.55, 0.55),  # Light grey (fallback)
    tile_top=TileRegistry.STONE_ANDESITE,
    tile_side=TileRegistry.STONE_ANDESITE,
    tile_bottom=TileRegistry.STONE_ANDESITE,
    display_name="Andesite"
))

BlockRegistry.register(Block(
    name="granite",
    color=(0.6, 0.5, 0.45),  # Pinkish grey (fallback)
    tile_top=TileRegistry.STONE_GRANITE,
    tile_side=TileRegistry.STONE_GRANITE,
    tile_bottom=TileRegistry.STONE_GRANITE,
    display_name="Granite"
))

