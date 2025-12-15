"""Player collision bounds definition and configuration."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from util.hot_config import HotConfig


@dataclass
class PlayerHitbox:
    """Defines the player's collision boundaries.
    
    The hitbox defines the physical space the player occupies for collision detection.
    Dimensions are in world units.
    """
    width: float = 0.6      # X dimension (shoulder width)
    height: float = 1.8     # Y dimension (foot to head)
    depth: float = 0.6      # Z dimension (front to back)
    foot_offset: float = 0.2  # Distance from entity origin to feet
    
    def get_half_extents(self) -> tuple:
        """Return half-extents for collision calculations."""
        return (self.width / 2, self.height / 2, self.depth / 2)


def get_hitbox(config: Optional['HotConfig'] = None) -> PlayerHitbox:
    """Get player hitbox with values from hot-config.
    
    Args:
        config: Optional HotConfig instance. If None, returns default hitbox.
    
    Returns:
        PlayerHitbox with configured or default values.
    """
    if not config:
        return PlayerHitbox()
    
    return PlayerHitbox(
        width=config.get("player_hitbox_width", 0.6),
        height=config.get("player_hitbox_height", 1.8),
        depth=config.get("player_hitbox_depth", 0.6),
        foot_offset=config.get("foot_offset", 0.2)
    )
