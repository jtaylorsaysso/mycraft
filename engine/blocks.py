"""Block type definitions and registry.

This module defines the core block types used in world generation.
Each block has a color (for immediate rendering) and an optional texture name
(stubbed for future texture implementation).

The colored block approach allows rapid prototyping and performance baselining
without texture asset management overhead.
"""

from dataclasses import dataclass
from typing import Optional, Dict


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
    tile_top=0,      # Grass top
    tile_side=3,     # Grass side
    tile_bottom=2,   # Dirt
    display_name="Grass"
))

BlockRegistry.register(Block(
    name="dirt",
    color=(0.5, 0.35, 0.2),  # Rich brown (fallback)
    tile_top=2,      # Dirt
    tile_side=2,     # Dirt
    tile_bottom=2,   # Dirt
    display_name="Dirt"
))

BlockRegistry.register(Block(
    name="stone",
    color=(0.5, 0.5, 0.5),  # Medium grey (fallback)
    tile_top=1,      # Stone
    tile_side=1,     # Stone
    tile_bottom=1,   # Stone
    display_name="Stone"
))

BlockRegistry.register(Block(
    name="sand",
    color=(0.9, 0.8, 0.5),  # Warm yellow (fallback)
    tile_top=18,     # Sand
    tile_side=18,    # Sand
    tile_bottom=18,  # Sand
    display_name="Sand"
))

BlockRegistry.register(Block(
    name="gravel",
    color=(0.4, 0.4, 0.4),  # Dark grey (fallback)
    tile_top=19,     # Gravel
    tile_side=19,    # Gravel
    tile_bottom=19,  # Gravel
    display_name="Gravel"
))

BlockRegistry.register(Block(
    name="snow",
    color=(0.95, 0.95, 0.98),  # Pure white with slight blue tint (fallback)
    tile_top=66,     # Snow
    tile_side=68,    # Snow side
    tile_bottom=2,   # Dirt
    display_name="Snow"
))

BlockRegistry.register(Block(
    name="clay",
    color=(0.7, 0.6, 0.5),  # Tan/beige (fallback)
    tile_top=2,      # Dirt (clay uses dirt texture)
    tile_side=2,     # Dirt
    tile_bottom=2,   # Dirt
    display_name="Clay"
))

BlockRegistry.register(Block(
    name="wood",
    color=(0.35, 0.25, 0.15),  # Dark brown (fallback)
    tile_top=21,     # Log top
    tile_side=20,    # Log side
    tile_bottom=21,  # Log top
    display_name="Wood"
))

