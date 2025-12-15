"""
MyCraft HUD (Heads-Up Display)

Displays useful information to the player:
- FPS counter
- Position (for debugging)
- Control hints
- Connection status (multiplayer)
- Player count (multiplayer)
"""

from ursina import Entity, Text, color, time, camera
from engine.input_handler import KeyBindings


class HUD:
    """Heads-up display showing game information and controls."""
    
    def __init__(self, player_entity, networking=False):
        """
        Initialize the HUD.
        
        Args:
            player_entity: Reference to the player entity for position tracking
            networking: Whether networking is enabled
        """
        self.player = player_entity
        self.networking = networking
        
        # Crosshair (center of screen) - improved visibility
        self.crosshair = Entity(
            parent=camera.ui,
            model='quad',
            scale=0.008,
            color=color.white,
            z=-1
        )
        
        # FPS Counter (top-right) with background
        self.fps_text = Text(
            text='FPS: --',
            position=(0.85, 0.48),
            origin=(0.5, 0.5),
            scale=1.2,
            color=color.white,
            background=True
        )
        
        # Position indicator (top-left, for debugging) - hidden by default
        self.pos_text = Text(
            text='Position: (0, 0, 0)',
            position=(-0.85, 0.48),
            origin=(-0.5, 0.5),
            scale=1.0,
            color=color.light_gray,
            background=True,
            enabled=False  # Hidden by default, toggle with F3
        )
        
        # Control hints (bottom-left) with background
        controls = [
            "Controls:",
            f"{KeyBindings.FORWARD}/{KeyBindings.LEFT}/{KeyBindings.BACK}/{KeyBindings.RIGHT} - Move",
            "Mouse - Look Around",
            f"{KeyBindings.JUMP} - Jump",
            f"{KeyBindings.TOGGLE_MOUSE} - Toggle Cursor",
            f"[1-6] - Quick Commands",
        ]
        
        if networking:
            controls.append(f"{KeyBindings.CMD} - Admin Console")
        
        self.controls_text = Text(
            text='\n'.join(controls),
            position=(-0.85, -0.35),
            origin=(-0.5, -0.5),
            scale=0.9,
            color=color.rgba(255, 255, 255, 200),
            background=True
        )
        
        # Welcome message (center, fades out after 8 seconds)
        self.welcome_message = Text(
            text='',
            position=(0, 0.15),
            origin=(0, 0),
            scale=1.1,
            color=color.yellow,
            background=True,
            enabled=False
        )
        self.welcome_timer = 0
        self.welcome_duration = 8.0
        
        # Connection status (top-center, only shown in multiplayer)
        self.connection_text = Text(
            text='',
            position=(0, 0.48),
            origin=(0, 0.5),
            scale=1.0,
            color=color.lime,
            enabled=networking,
            background=True
        )
        
        # Player count (below connection status)
        self.player_count_text = Text(
            text='',
            position=(0, 0.44),
            origin=(0, 0.5),
            scale=0.9,
            color=color.white,
            enabled=networking,
            background=True
        )
        
        # Loading indicator (bottom-center)
        self.loading_text = Text(
            text='',
            position=(0, -0.45),
            origin=(0, 0),
            scale=0.9,
            color=color.cyan,
            background=True,
            enabled=False
        )
        
        # FPS tracking
        self.fps_update_interval = 0.5  # Update FPS twice per second
        self.fps_timer = 0
        self.frame_count = 0
        self.last_fps = 0
        self.debug_visible = False
        
    def update(self):
        """Update HUD elements. Call this every frame."""
        # Update FPS with dynamic color coding
        self.fps_timer += time.dt
        self.frame_count += 1
        
        if self.fps_timer >= self.fps_update_interval:
            self.last_fps = int(self.frame_count / self.fps_timer)
            self.fps_text.text = f'FPS: {self.last_fps}'
            
            # Dynamic color based on performance
            if self.last_fps >= 45:
                self.fps_text.color = color.lime  # Good performance
            elif self.last_fps >= 30:
                self.fps_text.color = color.yellow  # Acceptable
            else:
                self.fps_text.color = color.red  # Poor performance
            
            self.fps_timer = 0
            self.frame_count = 0
        
        # Update position (only if debug visible)
        if self.player and self.debug_visible:
            x, y, z = int(self.player.x), int(self.player.y), int(self.player.z)
            self.pos_text.text = f'Position: ({x}, {y}, {z})'
        
        # Update welcome message fade timer
        if self.welcome_message.enabled:
            self.welcome_timer += time.dt
            if self.welcome_timer >= self.welcome_duration:
                self.welcome_message.enabled = False
                self.welcome_timer = 0
        
        # Update multiplayer info if networking is enabled
        if self.networking and hasattr(self.player, 'network_client'):
            client = self.player.network_client
            if client and client.is_connected():
                self.connection_text.text = '● Connected'
                self.connection_text.color = color.lime
                
                # Update player count
                remote_players = client.get_remote_players()
                total_players = len(remote_players) + 1  # +1 for local player
                self.player_count_text.text = f'Players: {total_players}'
            else:
                self.connection_text.text = '● Disconnected'
                self.connection_text.color = color.red
                self.player_count_text.text = ''
    
    def show_welcome_message(self, message: str):
        """
        Display a welcome message that fades after welcome_duration seconds.
        
        Args:
            message: The message to display
        """
        self.welcome_message.text = message
        self.welcome_message.enabled = True
        self.welcome_timer = 0
    
    def set_loading(self, loading: bool, message: str = "Generating terrain..."):
        """
        Show/hide the loading indicator.
        
        Args:
            loading: Whether to show the loading indicator
            message: Loading message to display
        """
        self.loading_text.enabled = loading
        if loading:
            self.loading_text.text = message
    
    def toggle_debug(self):
        """Toggle debug information visibility (position, etc.)."""
        self.debug_visible = not self.debug_visible
        self.pos_text.enabled = self.debug_visible
    
    def toggle_visibility(self, visible=None):
        """
        Toggle HUD visibility.
        
        Args:
            visible: If provided, set visibility to this value. Otherwise, toggle.
        """
        if visible is None:
            visible = not self.fps_text.enabled
        
        self.fps_text.enabled = visible
        self.controls_text.enabled = visible
        
        if self.networking:
            self.connection_text.enabled = visible
            self.player_count_text.enabled = visible
            
        self.crosshair.enabled = visible
        
        # Debug and welcome are controlled separately
    
    def hide_controls(self):
        """Hide the controls overlay (useful after player learns the game)."""
        self.controls_text.enabled = False
    
    def show_controls(self):
        """Show the controls overlay."""
        self.controls_text.enabled = True
