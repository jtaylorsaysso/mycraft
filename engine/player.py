from ursina import Entity, camera, color, Vec3, raycast, destroy, scene, Text, InputField, mouse
from engine.input_handler import InputHandler
from engine.hud import HUD
from engine.animation import AnimatedMannequin, AnimationController
from network.client import get_client
from engine.remote_player import RemotePlayer
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from util.hot_config import HotConfig

class Player(Entity):
    def __init__(self, start_pos=(0,2,0), networking: bool = False, sensitivity: float = 40.0, 
                 god_mode: bool = False, config: Optional['HotConfig'] = None, name: str = "Player"):
        # Player parent entity
        super().__init__(
            position=start_pos
        )
        self.config = config
        self.name = name
        
        # Networking setup
        self.networking = networking
        self.network_client = get_client() if networking else None
        
        if self.networking and self.network_client:
            self.network_client.send_name(self.name)
            
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

        # Animated mannequin with procedural animations
        self.mannequin = AnimatedMannequin(parent=self)
        self.animation_controller = AnimationController(self.mannequin, config=config)

        # Setup third-person camera
        self.setup_third_person_camera()
        
        # Initialize input handler with hot-config support
        self.input_handler = InputHandler(self, sensitivity=sensitivity, god_mode=god_mode, config=config)
        
        # Initialize HUD
        self.hud = HUD(self, networking=networking)
        
        # Register for config changes specific to player/camera
        if self.config:
            self.config.on_change(self._on_config_change)
        
        # CRITICAL: Force player onto ground after all initialization
        # This ensures Entity is fully created before positioning
        self._force_initial_ground_snap()

    def _on_config_change(self, key: str, value):
        """Handle config changes for camera parameters."""
        if key == "camera_distance":
            self.camera_offset.z = -float(value)
        elif key == "camera_height":
            self.camera_offset.y = float(value)
        elif key == "camera_side_offset":
            self.camera_offset.x = float(value)
        elif key == "fov":
            camera.fov = float(value)
        elif key == "camera_smoothing":
            self.camera_smoothing = float(value)
    
    def _force_initial_ground_snap(self):
        """Aggressively force player onto ground during initialization.
        
        This uses the world's procedural height function directly as a
        failsafe, bypassing raycasting entirely for initial spawn.
        """
        # Import here to avoid circular dependency
        from engine.game_app import _world
        
        if _world is None:
            print("⚠️  Cannot snap to ground: world not initialized")
            return
        
        # Get guaranteed ground height from procedural generation
        terrain_height = _world.get_height(int(self.x), int(self.z))
        target_y = terrain_height + 2.0  # 2 units above terrain
        
        # Force position
        self.y = target_y
        
        print(f"🔧 FORCED player ground snap: y={target_y:.1f} (terrain={terrain_height})")
        
        # Also reset physics state to be grounded
        if hasattr(self, 'input_handler') and hasattr(self.input_handler, '_physics_state'):
            self.input_handler._physics_state.velocity_y = 0.0
            self.input_handler._physics_state.grounded = True
        
    def setup_third_person_camera(self):
        """Create an over-the-shoulder third-person camera setup"""
        # Create a camera pivot at torso height (center of player)
        self.camera_pivot = Entity(parent=self, y=1.0)
        
        # Camera offset: right, up, back (so player appears on left side)
        # Use config defaults if available
        dist = 4.0
        height = 2.0
        side = 1.0
        fov = 60
        
        if self.config:
            dist = self.config.get("camera_distance", dist)
            height = self.config.get("camera_height", height)
            side = self.config.get("camera_side_offset", side)
            fov = self.config.get("fov", 90) # Default to 90 if using config
            
        self.camera_offset = Vec3(side, height, -dist)
        
        # Camera settings
        camera.parent = self.camera_pivot
        camera.position = self.camera_offset
        camera.fov = fov  # Field of view
        
        # Look ahead in facing direction
        target = self.camera_pivot.world_position + self.forward * 3
        camera.look_at(target)
        
        # Camera collision prevention settings
        self.min_camera_distance = 1.0
        self.camera_safety_margin = 0.1
        
        # Camera smoothing settings (load from config if available)
        self.camera_smoothing = self.config.get("camera_smoothing", 0.15) if self.config else 0.15
        self.last_camera_position = None  # Track for lerp
        
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
        
        # F3 to toggle debug info
        if key == 'f3':
            self.hud.toggle_debug()
            return

        self.input_handler.input(key)
        
    def update(self):
        """Delegate update logic to InputHandler and update camera"""
        from ursina import time
        dt = time.dt
        self.input_handler.update(dt)
        self.update_camera()
        
        # Update god mode visual feedback
        if hasattr(self.input_handler, 'god_mode'):
            if self.input_handler.god_mode:
                # Golden tint when in god mode
                self.mannequin.head.color = color.gold
                self.mannequin.torso.color = color.gold
                self.mannequin.right_arm.color = color.gold
                self.mannequin.left_arm.color = color.gold
                self.mannequin.right_leg.color = color.gold
                self.mannequin.left_leg.color = color.gold
            else:
                # Reset to normal color
                body_color = color.rgb(150, 125, 100)
                self.mannequin.head.color = body_color
                self.mannequin.torso.color = body_color
                self.mannequin.right_arm.color = body_color
                self.mannequin.left_arm.color = body_color
                self.mannequin.right_leg.color = body_color
                self.mannequin.left_leg.color = body_color
        
        # Update animations based on physics state
        self._update_animations(dt)
        
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
    
    def _update_animations(self, dt: float):
        """Update mannequin animations based on physics state."""
        # Get velocity from physics state
        physics = self.input_handler._physics_state
        velocity = Vec3(
            physics.velocity_x,
            physics.velocity_y,
            physics.velocity_z
        )
        grounded = physics.grounded
        
        # Let animation controller determine and run appropriate animation
        self.animation_controller.update(dt, velocity, grounded)
    
    def update_camera(self):
        """Update camera position with collision prevention and smoothing"""
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
        
        # Calculate target position (with collision adjustment if needed)
        if hit_info.hit:
            # Clamp camera to safe distance before obstacle
            clamped_dist = max(self.min_camera_distance, hit_info.distance - self.camera_safety_margin)
            target_position = origin + direction * clamped_dist
        else:
            # Use desired position
            target_position = desired_world_pos
        
        # Apply smoothing to camera movement
        if self.last_camera_position is None:
            # First frame, no smoothing
            camera.world_position = target_position
        else:
            # Lerp towards target position for smooth camera movement
            from ursina import lerp
            camera.world_position = lerp(
                self.last_camera_position,
                target_position,
                self.camera_smoothing
            )
        
        # Store current position for next frame
        self.last_camera_position = Vec3(camera.world_position)
        
        # Always look ahead in facing direction
        target = self.camera_pivot.world_position + self.forward * 3
        camera.look_at(target)

    # build_body() removed - now using AnimatedMannequin
    
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
            name = state.get('name', 'Unknown')
            
            # Use interpolation
            remote_entity.set_target(pos, rot_y)
            remote_entity.set_name(name)
    
    def create_remote_player(self):
        """Create a simple entity to represent a remote player."""
        return RemotePlayer(position=(0, 2, 0))