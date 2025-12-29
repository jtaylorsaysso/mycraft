"""Water block definitions and special properties."""

from games.voxel_world.blocks.blocks import Block, BlockRegistry
from dataclasses import dataclass

@dataclass
class WaterBlock(Block):
    """Extended block type for water with liquid properties."""
    
    is_transparent: bool = True
    is_liquid: bool = True
    wobble_enabled: bool = True
    alpha: float = 0.7
    water_level: int = 8  # 1-8, where 8 is full/source
    is_source: bool = True  # Source blocks don't drain
    
    def __post_init__(self):
        """Initialize water-specific properties."""
        super().__post_init__()
        # Water uses custom shader, no tile textures
        self.tile_top = None
        self.tile_side = None
        self.tile_bottom = None


# Register water block
water = WaterBlock(
    name="water",
    color=(0.2, 0.5, 0.8),  # Cyan-blue base color
    display_name="Water"
)

BlockRegistry.register(water)


# Helper functions for water queries
def is_water_block(block) -> bool:
    """Check if a block is water."""
    return hasattr(block, 'is_liquid') and block.is_liquid


def get_water_level(block) -> int:
    """Get water level (1-8) from a water block."""
    if hasattr(block, 'water_level'):
        return block.water_level
    return 0
