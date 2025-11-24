from ursina import Entity, camera, color, Vec3, raycast, destroy, scene, Text, InputField, mouse

from engine.input_handler import InputHandler
from network.client import get_client


class Player(Entity):
    def __init__(self, start_pos=(0,2,0), networking: bool = False):
        # Player parent entity
        super().__init__(
            position=start_pos
        )

        # Networking setup
        self._active_hitboxes = []
        self.camera_safety_margin = None
        self.min_camera_distance = None
        self.camera_offset = None
        self.camera_pivot = None
        self.networking = networking
        self.network_client = get_client() if networking else None
        self.send_rate = 10  # Send updates 10 times per second
        self.last_send_time = 0
        
        # Remote players storage
        self.remote_players = {}

        # Player health and damage
        self.hp = 10
        self.damage_cooldown = 0
        self.damage_cooldown_time = 1.0  # 1 second between hits

        # Admin console UI
        self.console_open = False
        self.console_max_lines = 8
        self.console_input = InputField(
            parent=camera.ui,
            position=(-0.45, -0.45),
            scale_x=0.9,
            scale_y=0.05,
            enabled=False,
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
        
        # Initialize input handler
        self.input_handler = InputHandler(self)
        
        # Simple attack state
        self.attack_cooldown = 0.0
        
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

        if key == 'left mouse down':
            self.attack()
            return

        self.input_handler.input(key)
        
    def update(self):
        """Delegate update logic to InputHandler and update camera"""
        from ursina import time
        dt = time.dt
        self.input_handler.update(dt)
        self.update_camera()
        
        # Update attack cooldown
        if self.attack_cooldown > 0.0:
            self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        
        # Update damage cooldown
        if self.damage_cooldown > 0.0:
            self.damage_cooldown = max(0.0, self.damage_cooldown - dt)
        
        # Clean up expired hitboxes and handle manual overlap checks
        if hasattr(self, '_active_hitboxes'):
            to_remove = []
            for hitbox in self._active_hitboxes:
                hitbox.life_time -= dt
                if hitbox.life_time <= 0:
                    destroy(hitbox)
                    to_remove.append(hitbox)
                    continue

                # Manual overlap check with slime entities
                for other in scene.entities:
                    if getattr(other, 'is_slime', False) and not getattr(other, 'is_dead', False):
                        # Simple distance-based overlap check
                        dist = (hitbox.world_position - other.world_position).length()
                        if dist < 2.0:  # increased threshold to account for offset
                            # Apply damage
                            other.hp = getattr(other, 'hp', 1) - 1

                            # Simple knockback away from player
                            knock_dir = (other.world_position - self.world_position).normalized()
                            other.position += knock_dir * 0.5

                            # Camera shake on hit
                            camera.shake(duration=0.2, magnitude=0.5)

                            # Flash slime white briefly
                            from ursina import invoke, curve
                            original_color = other.color
                            other.color = color.white
                            def restore_color():
                                other.color = original_color
                            invoke(restore_color, delay=0.1)

                            # Particle burst at impact point (safe pattern)
                            impact_pos = (hitbox.world_position + other.world_position) / 2
                            for i in range(6):
                                particle = Entity(
                                    model='quad',
                                    color=color.white,
                                    scale=0,
                                    position=impact_pos,
                                    add_to_scene_entities=False
                                )
                                import random
                                offset = Vec3(
                                    random.uniform(-0.3, 0.3),
                                    random.uniform(-0.3, 0.3),
                                    random.uniform(-0.3, 0.3)
                                )
                                particle.position += offset
                                particle.animate_scale(0.2, 0.3, curve=curve.out_expo)
                                particle.animate_color(color.clear, duration=0.3, curve=curve.out_expo)
                                destroy(particle, delay=0.3)

                            if other.hp <= 0:
                                other.is_dead = True
                                destroy(other)

                            destroy(hitbox)
                            to_remove.append(hitbox)
                            break

            for hb in to_remove:
                if hb in self._active_hitboxes:
                    self._active_hitboxes.remove(hb)
        
        # Check collision damage with slimes
        if self.damage_cooldown <= 0:
            for other in scene.entities:
                if getattr(other, 'is_slime', False) and not getattr(other, 'is_dead', False):
                    dist = (self.world_position - other.world_position).length()
                    if dist < 1.0:  # touching
                        self.hp -= 1
                        self.damage_cooldown = self.damage_cooldown_time
                        # Knockback away from slime
                        knock_dir = (self.world_position - other.world_position).normalized()
                        self.position += knock_dir * 2.0
                        print("Applying knockback and visual feedback")
                        # Camera shake on hit
                        camera.shake(duration=0.2, magnitude=0.5)
                        # Simple UI overlay flash
                        from ursina import Entity, invoke
                        flash = Entity(
                            parent=camera.ui,
                            model='quad',
                            color=color.rgba(255, 0, 0, 64),
                            scale=2,
                            z=-1
                        )
                        invoke(destroy, flash, delay=0.1)
                        print(f"Player hit! HP: {self.hp}")
                        if self.hp <= 0:
                            print("Player defeated!")
                            # Simple respawn for demo
                            self.position = (8, 2, 4)
                            self.hp = 10
                        break
        
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
        
        # Ray cast from pivot to desired position
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

        #Torso
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(150, 125, 100),
            scale=(0.3, 1.2, 0.4),
            y=0.9

        )

        #Legs
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
            
            remote_entity.position = pos
            remote_entity.rotation_y = rot_y
    
    def create_remote_player(self):
        """Create a simple entity to represent a remote player."""
        # Simple colored cube to represent other players
        remote = Entity(
            model='cube',
            color=color.azure,
            scale=(0.3, 1.8, 0.3),
            position=(0, 2, 0)
        )
        return remote

    def attack(self):
        """Spawn a short-lived sword hitbox in front of the player."""

        # Basic cooldown to prevent spamming
        if self.attack_cooldown > 0.0:
            return

        self.attack_cooldown = 0.35

        # Position hitbox slightly in front of player and around slime mid-height
        forward = self.forward
        spawn_pos = self.world_position + forward * 1.5 + Vec3(0, 0.5, 0)  # increased forward offset

        hitbox = Entity(
            model='cube',
            color=color.rgba(255, 0, 0, 150),
            scale=(0.6, 0.6, 0.6),
            position=spawn_pos,
            collider='box',  # Keep collider for future collision work
        )

        hitbox.life_time = 0.2
        hitbox.owner = self

        # Store hitbox on player to update in Player.update instead of assigning a dynamic function
        if not hasattr(self, '_active_hitboxes'):
            self._active_hitboxes = []
        self._active_hitboxes.append(hitbox)