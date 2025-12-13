"""
MyCraft HUD (Heads-Up Display)

Displays useful information to the player:
- FPS counter
- Position (for debugging)
- Control hints
- Connection status (multiplayer)
- Player count (multiplayer)
"""

from ursina import Entity, Text, color, time


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
        
        # FPS Counter (top-right)
        self.fps_text = Text(
            text='FPS: --',
            position=(0.85, 0.48),
            origin=(0.5, 0.5),
            scale=1.2,
            color=color.white
        )
        
        # Position indicator (top-left, for debugging)
        self.pos_text = Text(
            text='Position: (0, 0, 0)',
            position=(-0.85, 0.48),
            origin=(-0.5, 0.5),
            scale=1.0,
            color=color.light_gray
        )
        
        # Control hints (bottom-left)
        controls = [
            "Controls:",
            "W/A/S/D - Move",
            "Mouse - Look Around",
            "Space - Jump",
            "Esc - Toggle Cursor"
        ]
        
        if networking:
            controls.append("/ - Admin Console")
        
        self.controls_text = Text(
            text='\n'.join(controls),
            position=(-0.85, -0.35),
            origin=(-0.5, -0.5),
            scale=0.9,
            color=color.rgba(255, 255, 255, 180)
        )
        
        # Connection status (top-center, only shown in multiplayer)
        self.connection_text = Text(
            text='',
            position=(0, 0.48),
            origin=(0, 0.5),
            scale=1.0,
            color=color.lime,
            enabled=networking
        )
        
        # Player count (below connection status)
        self.player_count_text = Text(
            text='',
            position=(0, 0.44),
            origin=(0, 0.5),
            scale=0.9,
            color=color.white,
            enabled=networking
        )
        
        # FPS tracking
        self.fps_update_interval = 0.5  # Update FPS twice per second
        self.fps_timer = 0
        self.frame_count = 0
        self.last_fps = 0
        
    def update(self):
        """Update HUD elements. Call this every frame."""
        # Update FPS
        self.fps_timer += time.dt
        self.frame_count += 1
        
        if self.fps_timer >= self.fps_update_interval:
            self.last_fps = int(self.frame_count / self.fps_timer)
            self.fps_text.text = f'FPS: {self.last_fps}'
            self.fps_timer = 0
            self.frame_count = 0
        
        # Update position
        if self.player:
            x, y, z = int(self.player.x), int(self.player.y), int(self.player.z)
            self.pos_text.text = f'Position: ({x}, {y}, {z})'
        
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
    
    def toggle_visibility(self, visible=None):
        """
        Toggle HUD visibility.
        
        Args:
            visible: If provided, set visibility to this value. Otherwise, toggle.
        """
        if visible is None:
            visible = not self.fps_text.enabled
        
        self.fps_text.enabled = visible
        self.pos_text.enabled = visible
        self.controls_text.enabled = visible
        
        if self.networking:
            self.connection_text.enabled = visible
            self.player_count_text.enabled = visible
    
    def hide_controls(self):
        """Hide the controls overlay (useful after player learns the game)."""
        self.controls_text.enabled = False
    
    def show_controls(self):
        """Show the controls overlay."""
        self.controls_text.enabled = True
