"""
AvatarColorSystem: Syncs AvatarColors component to VoxelAvatar visuals.

Updates temporary color timers and applies color changes to the avatar's
visual representation in real-time.
"""

from engine.ecs.system import System
from engine.components.avatar_colors import AvatarColors
from engine.core.logger import get_logger
from typing import Optional

logger = get_logger(__name__)


class AvatarColorSystem(System):
    """
    Syncs AvatarColors component state to VoxelAvatar visual nodes.
    
    Responsibilities:
    - Update temporary color timers
    - Apply body color changes
    - Apply per-bone color overrides
    - Handle temporary color effects (from projectiles)
    """
    
    def __init__(self, world, event_bus, game):
        """
        Initialize the avatar color system.
        
        Args:
            world: ECS world instance
            event_bus: Event bus for system communication
            game: VoxelGame instance (for accessing player mechanics)
        """
        super().__init__(world, event_bus)
        self.game = game
        self._last_synced_colors = {}  # Cache to avoid redundant updates
        
        # Register input for color cycling
        if hasattr(self.game, 'accept'):
            self.game.accept('c', self.cycle_body_color)
            
    def cycle_body_color(self):
        """Cycle through unlocked colors for the player's body."""
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            return
            
        colors = self.world.get_component(player_id, AvatarColors)
        if not colors:
            return
            
        # Find current color index
        from engine.color.palette import ColorPalette
        
        # Get all unlocked colors
        unlocked = colors.unlocked_colors
        if not unlocked:
            return
            
        # Find current index
        # Use current_color_name if valid
        if colors.current_color_name in unlocked:
            match_idx = unlocked.index(colors.current_color_name)
        else:
             # Fallback: find by RGBA
             current_rgba = colors.body_color
             for i, name in enumerate(unlocked):
                 c = ColorPalette.get_color(name)
                 if c and c.rgba == current_rgba:
                     match_idx = i
                     break
        
        # Next color
        next_idx = (match_idx + 1) % len(unlocked)
        next_name = unlocked[next_idx]
        next_color = ColorPalette.get_color(next_name)
        
        if next_color:
            colors.body_color = next_color.rgba
            colors.current_color_name = next_name
            logger.info(f"🎨 Switched body color to {next_name}")

    
    def update(self, dt: float):
        """
        Update avatar colors each frame.
        
        Args:
            dt: Delta time since last update
        """
        # Get player entity
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            return
        
        # Get AvatarColors component
        colors = self.world.get_component(player_id, AvatarColors)
        if not colors:
            return
        
        # Update temporary color timer
        colors.update_temp_timer(dt)
        
        # Get avatar from AnimationMechanic
        avatar = self._get_player_avatar()
        if not avatar:
            return
        
        # Sync colors to avatar
        self._sync_colors_to_avatar(avatar, colors)
    
    def _get_player_avatar(self):
        """
        Get the player's VoxelAvatar instance.
        
        Returns:
            VoxelAvatar instance or None if not available
        """
        # Access PlayerControlSystem to get AnimationMechanic
        from engine.systems.player_controller import PlayerControlSystem
        player_system = self.world.get_system_by_type("PlayerControlSystem")
        
        if not player_system:
            return None
        
        # Get AnimationMechanic from player mechanics
        for mechanic in player_system.mechanics:
            if mechanic.__class__.__name__ == "AnimationMechanic":
                return mechanic.avatar
        
        return None
    
    def _sync_colors_to_avatar(self, avatar, colors: AvatarColors):
        """
        Sync AvatarColors component to VoxelAvatar visuals.
        
        Args:
            avatar: VoxelAvatar instance
            colors: AvatarColors component
        """
        # If temporary color is active, apply to all bones
        if colors.temporary_color and colors.temp_timer > 0:
            # Apply temp color to all bones
            for bone_name in avatar.bone_nodes.keys():
                try:
                    avatar.set_bone_color(bone_name, colors.temporary_color)
                except ValueError:
                    pass  # Bone doesn't exist (shouldn't happen)
        else:
            # Apply body color
            avatar.set_body_color(colors.body_color)
            
            # Apply per-bone overrides
            for bone_name, rgba in colors.bone_colors.items():
                try:
                    avatar.set_bone_color(bone_name, rgba)
                except ValueError:
                    logger.warning(f"Attempted to color non-existent bone: {bone_name}")
