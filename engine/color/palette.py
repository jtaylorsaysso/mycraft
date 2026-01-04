"""
Color palette system for avatar customization.

Defines starter colors (available immediately) and loot colors
(unlockable through gameplay). Supports the color combat loop
where enemies drop color swatches as loot.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import random


@dataclass
class ColorSwatch:
    """A single color with metadata."""
    name: str
    rgba: Tuple[float, float, float, float]
    rarity: str = "common"  # common, rare, legendary
    
    def __post_init__(self):
        """Validate RGBA values are in valid range."""
        r, g, b, a = self.rgba
        if not all(0.0 <= v <= 1.0 for v in [r, g, b, a]):
            raise ValueError(f"RGBA values must be in range [0.0, 1.0], got {self.rgba}")


class ColorPalette:
    """
    Central color palette registry.
    
    Provides starter colors (available at game start) and loot colors
    (unlockable through defeating enemies, completing shrines, etc.).
    """
    
    # Starter colors - available immediately at game start
    STARTER_COLORS: Dict[str, ColorSwatch] = {
        "red": ColorSwatch("Red", (0.9, 0.2, 0.2, 1.0), "common"),
        "blue": ColorSwatch("Blue", (0.2, 0.4, 0.9, 1.0), "common"),
        "yellow": ColorSwatch("Yellow", (0.9, 0.9, 0.2, 1.0), "common"),
        "green": ColorSwatch("Green", (0.2, 0.8, 0.2, 1.0), "common"),
        "orange": ColorSwatch("Orange", (0.9, 0.5, 0.1, 1.0), "common"),
        "purple": ColorSwatch("Purple", (0.6, 0.2, 0.8, 1.0), "common"),
        "white": ColorSwatch("White", (0.9, 0.9, 0.9, 1.0), "common"),
        "black": ColorSwatch("Black", (0.15, 0.15, 0.15, 1.0), "common"),
    }
    
    # Loot colors - unlockable through gameplay
    LOOT_COLORS: Dict[str, ColorSwatch] = {
        # Rare hues
        "crimson": ColorSwatch("Crimson", (0.7, 0.0, 0.0, 1.0), "rare"),
        "navy": ColorSwatch("Navy", (0.0, 0.0, 0.5, 1.0), "rare"),
        "gold": ColorSwatch("Gold", (1.0, 0.84, 0.0, 1.0), "rare"),
        "silver": ColorSwatch("Silver", (0.75, 0.75, 0.75, 1.0), "rare"),
        
        # Natural colors
        "forest": ColorSwatch("Forest", (0.13, 0.55, 0.13, 1.0), "common"),
        "coral": ColorSwatch("Coral", (1.0, 0.5, 0.31, 1.0), "common"),
        "teal": ColorSwatch("Teal", (0.0, 0.5, 0.5, 1.0), "common"),
        
        # Metallics
        "bronze": ColorSwatch("Bronze", (0.8, 0.5, 0.2, 1.0), "rare"),
        "charcoal": ColorSwatch("Charcoal", (0.21, 0.27, 0.31, 1.0), "common"),
        
        # Soft colors
        "lavender": ColorSwatch("Lavender", (0.9, 0.9, 0.98, 1.0), "common"),
        "peach": ColorSwatch("Peach", (1.0, 0.9, 0.71, 1.0), "common"),
        "mint": ColorSwatch("Mint", (0.62, 0.99, 0.6, 1.0), "common"),
    }
    
    @classmethod
    def get_color(cls, name: str) -> Optional[ColorSwatch]:
        """
        Get a color by name from either starter or loot palette.
        
        Args:
            name: Color name (case-insensitive)
            
        Returns:
            ColorSwatch if found, None otherwise
        """
        name_lower = name.lower()
        
        # Check starter colors first
        if name_lower in cls.STARTER_COLORS:
            return cls.STARTER_COLORS[name_lower]
        
        # Check loot colors
        if name_lower in cls.LOOT_COLORS:
            return cls.LOOT_COLORS[name_lower]
        
        return None
    
    @classmethod
    def get_random_loot_color(cls, rng: Optional[random.Random] = None) -> ColorSwatch:
        """
        Get a random color from the loot palette.
        
        Args:
            rng: Random number generator (uses default if None)
            
        Returns:
            Random ColorSwatch from loot palette
        """
        if rng is None:
            rng = random.Random()
        
        color_name = rng.choice(list(cls.LOOT_COLORS.keys()))
        return cls.LOOT_COLORS[color_name]
    
    @classmethod
    def get_all_colors(cls) -> Dict[str, ColorSwatch]:
        """Get all colors (starter + loot) as a single dictionary."""
        return {**cls.STARTER_COLORS, **cls.LOOT_COLORS}
    
    @classmethod
    def get_starter_color_names(cls) -> list[str]:
        """Get list of starter color names."""
        return list(cls.STARTER_COLORS.keys())
    
    @classmethod
    def get_loot_color_names(cls) -> list[str]:
        """Get list of loot color names."""
        return list(cls.LOOT_COLORS.keys())
