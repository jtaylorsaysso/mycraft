"""
MyCraft HUD (Heads-Up Display) - Panda3D Native

Displays useful information to the player:
- FPS counter
- Position (for debugging)
- Control hints
- Connection status (multiplayer)
- Player count (multiplayer)
"""

from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame
from panda3d.core import TextNode, LVector3f
from typing import Optional
from engine.ui.settings_overlay import SettingsOverlay
from engine.core.hot_config import HotConfig

class HUD:
    """Heads-up display showing game information and controls using Panda3D DirectGUI."""
    
    def __init__(self, base, player_entity_id: Optional[str] = None, world=None, networking=False, hot_config=None):
        """
        Initialize the HUD.
        
        Args:
            base: ShowBase instance
            player_entity_id: Entity ID of the player for position tracking
            world: ECS World instance for component access
            networking: Whether networking is enabled
            hot_config: Optional HotConfig instance for settings
        """
        self.base = base
        self.player_entity_id = player_entity_id
        self.world = world
        self.networking = networking
        self.hot_config = hot_config
        
        # Settings Overlay
        if self.hot_config:
            self.settings = SettingsOverlay(base, self.hot_config)
            self.settings.hide()
        else:
            self.settings = None
        
        # Crosshair (center of screen)
        self.crosshair = OnscreenText(
            text='+',
            pos=(0, 0),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=False
        )
        
        # FPS Counter (top-right) 
        self.fps_text = OnscreenText(
            text='FPS: --',
            pos=(1.3, 0.9),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
            mayChange=True
        )
        
        # Position indicator (top-left, for debugging) - hidden by default
        self.pos_text = OnscreenText(
            text='Position: (0, 0, 0)',
            pos=(-1.3, 0.9),
            scale=0.04,
            fg=(0.7, 0.7, 0.7, 1),
            align=TextNode.ALeft,
            mayChange=True
        )
        self.pos_text.hide()
        
        # Control hints (bottom-left)
        controls = [
            "Controls:",
            "W/A/S/D - Move",
            "Mouse - Look Around",
            "Space - Jump",
            "Shift - Dodge (combat) / Crouch",
            "V - Toggle Camera",
            "",
            "Combat:",
            "Mouse 1 - Attack",
            "Mouse 2 - Parry",
            "R - Throw Color",
            "",
            "Esc - Pause Menu",
        ]
        
        if networking:
            controls.append("/ - Admin Console")
        
        self.controls_text = OnscreenText(
            text='\n'.join(controls),
            pos=(-1.3, -0.6),
            scale=0.04,
            fg=(1, 1, 1, 0.8),
            align=TextNode.ALeft,
            mayChange=False
        )
        
        # Welcome message (center, fades out after duration)
        self.welcome_message = OnscreenText(
            text='',
            pos=(0, 0.3),
            scale=0.06,
            fg=(1, 1, 0, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        self.welcome_message.hide()
        self.welcome_timer = 0
        self.welcome_duration = 8.0
        
        # Connection status (top-center, only shown in multiplayer)
        self.connection_text = OnscreenText(
            text='',
            pos=(0, 0.9),
            scale=0.045,
            fg=(0, 1, 0, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        if not networking:
            self.connection_text.hide()
        
        # Player count (below connection status)
        self.player_count_text = OnscreenText(
            text='',
            pos=(0, 0.85),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        if not networking:
            self.player_count_text.hide()
        
        # Loading indicator (bottom-center)
        self.loading_text = OnscreenText(
            text='',
            pos=(0, -0.8),
            scale=0.045,
            fg=(0, 1, 1, 1),
            align=TextNode.ACenter,
            mayChange=True
        )
        self.loading_text.hide()
        
        # FPS tracking
        self.fps_update_interval = 0.5  # Update FPS twice per second
        self.fps_timer = 0
        self.frame_count = 0
        self.last_fps = 0
        self.debug_visible = False
        
        # Color Indicator (bottom-center) - shows current throwable color
        self.color_indicator_frame = DirectFrame(
            frameColor=(0, 0, 0, 0.5),
            frameSize=(-0.08, 0.08, -0.08, 0.08),
            pos=(0, 0, -0.85)
        )
        self.color_indicator = DirectFrame(
            parent=self.color_indicator_frame,
            frameColor=(0.2, 0.8, 0.2, 1.0),  # Default green
            frameSize=(-0.06, 0.06, -0.06, 0.06),
            pos=(0, 0, 0)
        )
        
        # Cooldown bar (below color indicator)
        self.cooldown_bar_bg = DirectFrame(
            frameColor=(0.2, 0.2, 0.2, 0.8),
            frameSize=(-0.08, 0.08, -0.015, 0.015),
            pos=(0, 0, -0.95)
        )
        self.cooldown_bar_fill = DirectFrame(
            parent=self.cooldown_bar_bg,
            frameColor=(1, 1, 1, 0.9),
            frameSize=(-0.08, 0.08, -0.012, 0.012),
            pos=(0, 0, 0)
        )
        
        # Color indicator label
        self.color_label = OnscreenText(
            text='R',
            pos=(0, -0.95),
            scale=0.03,
            fg=(1, 1, 1, 0.7),
            align=TextNode.ACenter,
            mayChange=False
        )
        
    def update(self, dt: float):
        """Update HUD elements. Call this every frame.
        
        Args:
            dt: Delta time since last frame
        """
        # Update FPS with dynamic color coding
        self.fps_timer += dt
        self.frame_count += 1
        
        if self.fps_timer >= self.fps_update_interval:
            self.last_fps = int(self.frame_count / self.fps_timer)
            self.fps_text.setText(f'FPS: {self.last_fps}')
            
            # Dynamic color based on performance
            if self.last_fps >= 45:
                self.fps_text.setFg((0, 1, 0, 1))  # Green - good performance
            elif self.last_fps >= 30:
                self.fps_text.setFg((1, 1, 0, 1))  # Yellow - acceptable
            else:
                self.fps_text.setFg((1, 0, 0, 1))  # Red - poor performance
            
            self.fps_timer = 0
            self.frame_count = 0
        
        # Update position (only if debug visible and we have world access)
        if self.debug_visible and self.world and self.player_entity_id:
            from engine.components.core import Transform
            transform = self.world.get_component(self.player_entity_id, Transform)
            if transform:
                pos = transform.position
                x, y, z = int(pos.x), int(pos.y), int(pos.z)
                # Get current biome
                try:
                    from games.voxel_world.biomes.biomes import BiomeRegistry
                    biome = BiomeRegistry.get_biome_at(x, y)  # y is depth in Panda3D
                    biome_name = biome.display_name
                except:
                    biome_name = "Unknown"
                self.pos_text.setText(f'Pos: ({x}, {y}, {z}) | Biome: {biome_name}')
        
        # Update welcome message fade timer
        if not self.welcome_message.isHidden():
            self.welcome_timer += dt
            if self.welcome_timer >= self.welcome_duration:
                self.welcome_message.hide()
                self.welcome_timer = 0
        
        # Update color indicator and cooldown bar
        if self.world and self.player_entity_id:
            from engine.components.avatar_colors import AvatarColors
            from engine.color.palette import ColorPalette
            
            colors = self.world.get_component(self.player_entity_id, AvatarColors)
            if colors:
                # Update color indicator
                color_name = colors.current_color_name
                color_def = ColorPalette.get_color(color_name)
                if color_def:
                    r, g, b, a = color_def.rgba
                    self.color_indicator['frameColor'] = (r, g, b, 1.0)
            
            # Update cooldown bar (get from PlayerControlSystem if available)
            # We need to access cooldown from the system - use event bus or store on component
            # For now, check if there's a cooldown attribute on AvatarColors or use a simple approach
            # HACK: Store cooldown on world temporarily
            cooldown_ratio = getattr(self.world, '_projectile_cooldown_ratio', 1.0)
            # Bar grows from center outward
            bar_half_width = 0.08 * cooldown_ratio
            self.cooldown_bar_fill['frameSize'] = (-bar_half_width, bar_half_width, -0.012, 0.012)
        
        # Update multiplayer info if networking is enabled
        # TODO: Wire up to actual network client when needed
    
    def show_welcome_message(self, message: str):
        """
        Display a welcome message that fades after welcome_duration seconds.
        
        Args:
            message: The message to display
        """
        self.welcome_message.setText(message)
        self.welcome_message.show()
        self.welcome_timer = 0
    
    def set_loading(self, loading: bool, message: str = "Generating terrain..."):
        """
        Show/hide the loading indicator.
        
        Args:
            loading: Whether to show the loading indicator
            message: Loading message to display
        """
        if loading:
            self.loading_text.setText(message)
            self.loading_text.show()
        else:
            self.loading_text.hide()
    
    def toggle_settings(self):
        """Toggle settings overlay visibility."""
        if self.settings:
            # Hide controls when settings are open
            if not self.settings.visible:
                self.settings.show()
                self.hide_controls()
            else:
                self.settings.hide()
                self.show_controls()

    def toggle_debug(self):
        """Toggle debug information visibility (position, etc.)."""
        self.debug_visible = not self.debug_visible
        if self.debug_visible:
            self.pos_text.show()
        else:
            self.pos_text.hide()
    
    def toggle_visibility(self, visible: Optional[bool] = None):
        """
        Toggle HUD visibility.
        
        Args:
            visible: If provided, set visibility to this value. Otherwise, toggle.
        """
        if visible is None:
            visible = self.fps_text.isHidden()
        
        if visible:
            self.fps_text.show()
            self.controls_text.show()
            self.crosshair.show()
            if self.networking:
                self.connection_text.show()
                self.player_count_text.show()
        else:
            self.fps_text.hide()
            self.controls_text.hide()
            self.crosshair.hide()
            if self.networking:
                self.connection_text.hide()
                self.player_count_text.hide()
    
    def hide_controls(self):
        """Hide the controls overlay (useful after player learns the game)."""
        self.controls_text.hide()
    
    def show_controls(self):
        """Show the controls overlay."""
        self.controls_text.show()
    
    def cleanup(self):
        """Remove all HUD elements from scene."""
        self.crosshair.destroy()
        self.fps_text.destroy()
        self.pos_text.destroy()
        self.controls_text.destroy()
        self.welcome_message.destroy()
        self.connection_text.destroy()
        self.player_count_text.destroy()
        self.loading_text.destroy()
        
        # Color indicator cleanup
        self.color_indicator_frame.destroy()
        self.cooldown_bar_bg.destroy()
        self.color_label.destroy()
        
        if self.settings:
            self.settings.frame.destroy()
