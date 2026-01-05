"""
AvatarColors ECS component for color customization.

Stores color state for avatars, including body color, per-bone overrides,
temporary color effects (from projectiles), and unlocked color collection.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from engine.ecs.component import Component


@dataclass
class AvatarColors(Component):
    """
    Color state for an avatar entity.
    
    Supports:
    - Base body color (default for all bones)
    - Per-bone color overrides
    - Temporary color effects (60s from color projectiles)
    - Unlocked color collection (for customization UI)
    """
    
    # Base color applied to all bones (unless overridden)
    body_color: Tuple[float, float, float, float] = (0.2, 0.8, 0.2, 1.0)
    current_color_name: str = "green" # Track name for projectiles
    
    # Per-bone color overrides (bone_name -> RGBA)
    bone_colors: Dict[str, Tuple[float, float, float, float]] = field(default_factory=dict)
    
    # Temporary color override (from color projectiles)
    temporary_color: Optional[Tuple[float, float, float, float]] = None
    temp_timer: float = 0.0  # Seconds remaining
    
    # Unlocked colors (color names from ColorPalette)
    unlocked_colors: List[str] = field(default_factory=lambda: [
        # Start with all starter colors unlocked
        "red", "blue", "yellow", "green", "orange", "purple", "white", "black"
    ])
    
    def get_effective_color(self, bone_name: str) -> Tuple[float, float, float, float]:
        """
        Get the effective display color for a bone.
        
        Priority:
        1. Temporary color (if active)
        2. Per-bone override
        3. Body color
        
        Args:
            bone_name: Name of the bone
            
        Returns:
            RGBA tuple for the bone
        """
        # Temporary color overrides everything
        if self.temporary_color is not None and self.temp_timer > 0:
            return self.temporary_color
        
        # Per-bone override
        if bone_name in self.bone_colors:
            return self.bone_colors[bone_name]
        
        # Default to body color
        return self.body_color
    
    def unlock_color(self, color_name: str) -> bool:
        """
        Unlock a new color for customization.
        
        Args:
            color_name: Name of color to unlock
            
        Returns:
            True if newly unlocked, False if already unlocked
        """
        if color_name not in self.unlocked_colors:
            self.unlocked_colors.append(color_name)
            return True
        return False
    
    def has_color(self, color_name: str) -> bool:
        """Check if a color is unlocked."""
        return color_name in self.unlocked_colors
    
    def apply_temporary_color(self, rgba: Tuple[float, float, float, float], duration: float = 60.0):
        """
        Apply a temporary color override (e.g., from color projectile).
        
        Args:
            rgba: Color to apply
            duration: Duration in seconds (default 60s)
        """
        self.temporary_color = rgba
        self.temp_timer = duration
    
    def clear_temporary_color(self):
        """Clear temporary color effect."""
        self.temporary_color = None
        self.temp_timer = 0.0
    
    def update_temp_timer(self, dt: float):
        """
        Update temporary color timer.
        
        Args:
            dt: Delta time in seconds
        """
        if self.temp_timer > 0:
            self.temp_timer -= dt
            if self.temp_timer <= 0:
                self.clear_temporary_color()
