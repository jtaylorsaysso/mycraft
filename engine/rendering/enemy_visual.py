"""
Enemy Visual system.

Handles the visual representation of enemies, including:
- Avatar creation (reusing VoxelAvatar)
- Color tinting based on loot drops
- Visual updates based on state
"""

from typing import Optional, Tuple
from panda3d.core import NodePath, LColor
from engine.color.palette import ColorPalette
from engine.animation.voxel_avatar import VoxelAvatar

class EnemyVisual:
    """
    Visual wrapper for an enemy entity.
    
    Composes a VoxelAvatar and applies enemy-specific visual effects
    like color tinting.
    """
    
    def __init__(self, node: NodePath, enemy_type: str, tint_color_name: str):
        """
        Initialize enemy visual.
        
        Args:
            node: Parent node to attach to
            enemy_type: Type of enemy (skeleton, zombie)
            tint_color_name: Name of color to tint with
        """
        self.root = node
        self.enemy_type = enemy_type
        
        # Create avatar
        # We reuse VoxelAvatar for the humanoid shape
        self.avatar = VoxelAvatar(self.root)
        
        # Base colors
        self.base_color = self._get_base_color(enemy_type)
        self.tint_strength = self._get_tint_strength(enemy_type)
        
        # Apply visual customization
        self._apply_appearance(tint_color_name)
        
    def _get_base_color(self, enemy_type: str) -> Tuple[float, float, float, float]:
        """Get base color for enemy type."""
        if enemy_type == "zombie":
            return (0.4, 0.5, 0.4, 1.0)  # Decay green
        # Default skeleton
        return (0.9, 0.9, 0.85, 1.0)     # Bone white
        
    def _get_tint_strength(self, enemy_type: str) -> float:
        """Get tint strength for enemy type."""
        if enemy_type == "zombie":
            return 0.6  # Strong tint on flesh
        return 0.4      # Subtle tint on bone
        
    def _apply_appearance(self, tint_name: str):
        """Apply colors and tinting."""
        # Get tint color
        tint_def = ColorPalette.get_color(tint_name)
        tint_rgba = tint_def.rgba if tint_def else (1, 1, 1, 1)
        
        # Blend base and tint
        r = self.base_color[0] * (1 - self.tint_strength) + tint_rgba[0] * self.tint_strength
        g = self.base_color[1] * (1 - self.tint_strength) + tint_rgba[1] * self.tint_strength
        b = self.base_color[2] * (1 - self.tint_strength) + tint_rgba[2] * self.tint_strength
        a = 1.0
        
        final_color = (r, g, b, a)
        
        # Apply to all bones
        self.avatar.set_body_color(final_color)
        
        # Determine head geometry style based on type
        # For now VoxelAvatar is generic, but we could toggle visibility of parts
        # e.g. self.avatar.set_feature_visibility('ears', False)
        
    def destroy(self):
        """Clean up visual resources."""
        if self.avatar:
            self.avatar.destroy()
            self.avatar = None
