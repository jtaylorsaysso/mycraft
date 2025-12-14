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
        color: RGB tuple (0.0-1.0 range) for colored rendering
        texture: Optional texture name for future implementation
        display_name: Human-readable name for UI/debugging
    """
    name: str
    color: tuple[float, float, float]
    texture: Optional[str] = None
    display_name: str = ""
    
    def __post_init__(self):
        """Set display_name from name if not provided."""
        if not self.display_name:
            self.display_name = self.name.capitalize()


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

BlockRegistry.register(Block(
    name="grass",
    color=(0.4, 0.7, 0.3),  # Vibrant green
    texture="grass",
    display_name="Grass"
))

BlockRegistry.register(Block(
    name="dirt",
    color=(0.5, 0.35, 0.2),  # Rich brown
    texture="dirt",
    display_name="Dirt"
))

BlockRegistry.register(Block(
    name="stone",
    color=(0.5, 0.5, 0.5),  # Medium grey
    texture="stone",
    display_name="Stone"
))

BlockRegistry.register(Block(
    name="sand",
    color=(0.9, 0.8, 0.5),  # Warm yellow
    texture="sand",
    display_name="Sand"
))

BlockRegistry.register(Block(
    name="gravel",
    color=(0.4, 0.4, 0.4),  # Dark grey
    texture="gravel",
    display_name="Gravel"
))

BlockRegistry.register(Block(
    name="snow",
    color=(0.95, 0.95, 0.98),  # Pure white with slight blue tint
    texture="snow",
    display_name="Snow"
))

BlockRegistry.register(Block(
    name="clay",
    color=(0.7, 0.6, 0.5),  # Tan/beige
    texture="clay",
    display_name="Clay"
))

BlockRegistry.register(Block(
    name="wood",
    color=(0.35, 0.25, 0.15),  # Dark brown
    texture="wood",
    display_name="Wood"
))
