from ursina import Entity, camera, color, Vec3, raycast, destroy, scene, Text, InputField, mouse
from engine.input_handler import InputHandler
from engine.hud import HUD
from network.client import get_client
from engine.remote_player import RemotePlayer
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from util.hot_config import HotConfig

class Player(Entity):
    def __init__(self, start_pos=(0,2,0), networking: bool = False, sensitivity: float = 40.0, 
                 god_mode: bool = False, config: Optional['HotConfig'] = None):
        # Player parent entity
        super().__init__(
            position=start_pos
        )

        # Networking setup
        self.networking = networking
        self.network_client = get_client() if networking else None
        self.send_rate = 10  # Send updates 10 times per second
        self.last_send_time = 0
        
        # Remote players storage
        self.remote_players = {}

        # Admin console UI
        self.console_open = False
        self.console_max_lines = 8
        self.console_input = InputField(
            parent=camera.ui,
            position=(-0.45, -0.45),
            scale_x=0.9,
            scale_y=0.05,
            enabled=False,
            hide_char='*',
            cursor='|'
        )
        self.console_log = Text(
            parent=camera.ui,
            text="",
            position=(-0.45, -0.3),
            origin=(-0.5, -0.5),
            scale=0.7,
        )

        # Basic mannequin: 3 stacked cubes
        self.build_body()

        # Setup third-person camera
        self.setup_third_person_camera()
        
        # Initialize input handler with hot-config support
        self.input_handler = InputHandler(self, sensitivity=sensitivity, god_mode=god_mode, config=config)
        
        # Initialize HUD
        self.hud = HUD(self, networking=networking)
        
    def setup_third_person_camera(self):
        """Create an over-the-shoulder third-person camera setup"""
        # Create a camera pivot at torso height (center of player)
        self.camera_pivot = Entity(parent=self, y=1.0)
        
        # Camera offset: right, up, back (so player appears on left side)
        self.camera_offset = Vec3(1, 2, -4)
        
        # Camera settings
        camera.parent = self.camera_pivot
        camera.position = self.camera_offset
        camera.fov = 60  # Field of view
        
        # Look ahead in facing direction
        target = self.camera_pivot.world_position + self.forward * 3
        camera.look_at(target)
        
        # Camera collision prevention settings
        self.min_camera_distance = 1.0
        self.camera_safety_margin = 0.1
        
    def input(self, key):
        if key == '/':
            if self.networking and self.network_client:
                self.console_open = not self.console_open
                self.console_input.enabled = self.console_open
                self.console_input.active = self.console_open
                mouse.locked = not self.console_open
            return

        if self.console_open:
            if key == 'enter':
                if self.networking and self.network_client:
                    command = self.console_input.text
                    self.console_input.text = ""
                    self.network_client.send_admin_command(command)
                return
            return

        self.input_handler.input(key)
        
    def update(self):
        """Delegate update logic to InputHandler and update camera"""
        from ursina import time
        dt = time.dt
        self.input_handler.update(dt)
        self.update_camera()
        
        # Update HUD
        self.hud.update()
        
        # Handle networking
        if self.networking and self.network_client:
            self.update_networking(dt)
            self.update_remote_players()

            # Update admin console scrollback from client log
            log_lines = self.network_client.get_admin_log()
            if log_lines:
                self.console_log.text = "\n".join(log_lines[-self.console_max_lines:])
    
    def update_camera(self):
        """Update camera position with collision prevention"""
        # Calculate desired world position
        desired_world_pos = (
            self.camera_pivot.world_position +
            self.camera_pivot.right * self.camera_offset.x +
            self.camera_pivot.up * self.camera_offset.y +
            self.camera_pivot.back * abs(self.camera_offset.z)
        )
        
        # Raycast from pivot to desired position
        origin = self.camera_pivot.world_position
        direction = (desired_world_pos - origin).normalized()
        distance = (desired_world_pos - origin).length()
        
        # Check for collisions (ignore player and its parts)
        hit_info = raycast(origin, direction, distance=distance, ignore=[self])
        
        if hit_info.hit:
            # Clamp camera to safe distance before obstacle
            clamped_dist = max(self.min_camera_distance, hit_info.distance - self.camera_safety_margin)
            camera.world_position = origin + direction * clamped_dist
        else:
            # Use desired position
            camera.world_position = desired_world_pos
        
        # Always look ahead in facing direction
        target = self.camera_pivot.world_position + self.forward * 3
        camera.look_at(target)

    def build_body(self):
        # Head
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(150, 125, 100),
            scale=0.3,
            y=1.6
        )

        # Torso
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(150, 125, 100),
            scale=(0.3, 1.2, 0.4),
            y=0.9
        )

        # Right Arm
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(150, 125, 100),
            scale=(0.15, 1.0, 0.15),
            position=(0.25, 0.9, 0)
        )

        # Left Arm
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(150, 125, 100),
            scale=(0.15, 1.0, 0.15),
            position=(-0.25, 0.9, 0)
        )

        # Legs
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(150, 125, 100),
            scale=(0.3, 1, 0.4),
            y=0.3
        )
    
    def update_networking(self, dt):
        """Send position updates to server at controlled rate."""
        if not self.network_client or not self.network_client.is_connected():
            return
        
        self.last_send_time += dt
        if self.last_send_time >= 1.0 / self.send_rate:
            # Send current position and rotation
            pos = [self.x, self.y, self.z]
            self.network_client.send_state_update(pos, self.rotation_y)
            self.last_send_time = 0
    
    def update_remote_players(self):
        """Update remote player entities based on server data."""
        if not self.network_client:
            return
        
        remote_data = self.network_client.get_remote_players()
        
        # Remove players that no longer exist
        for player_id in list(self.remote_players.keys()):
            if player_id not in remote_data:
                # Remove the entity
                if self.remote_players[player_id] in scene.children:
                    destroy(self.remote_players[player_id])
                del self.remote_players[player_id]
        
        # Update or create remote player entities
        for player_id, state in remote_data.items():
            if player_id not in self.remote_players:
                # Create new remote player entity
                self.remote_players[player_id] = self.create_remote_player()
            
            # Update position and rotation
            remote_entity = self.remote_players[player_id]
            pos = state.get('pos', [0, 0, 0])
            rot_y = state.get('rot_y', 0)
            
            # Use interpolation
            remote_entity.set_target(pos, rot_y)
    
    def create_remote_player(self):
        """Create a simple entity to represent a remote player."""
        return RemotePlayer(position=(0, 2, 0))