from ursina import held_keys, mouse, Vec3, camera
from ursina import time
import math
from typing import Optional, TYPE_CHECKING

from engine.physics import (
    KinematicState,
    apply_gravity,
    integrate_movement,
    simple_flat_ground_check,
    perform_jump,
    update_timers,
    register_jump_press,
    can_consume_jump,
    raycast_ground_height,
    raycast_wall_check,
)

if TYPE_CHECKING:
    from util.session_recorder import SessionRecorder, SessionPlayer
    from util.hot_config import HotConfig


class InputHandler:
    def __init__(self, player_entity, sensitivity: float = 40.0, god_mode: bool = False,
                 config: Optional['HotConfig'] = None):
        self.player = player_entity
        self.mouse_sensitivity = sensitivity
        self.god_mode = god_mode
        self._config = config
        
        # Session recording/replay
        self._recorder: Optional['SessionRecorder'] = None
        self._session_player: Optional['SessionPlayer'] = None
        self._last_mouse_velocity = (0, 0)
        
        self.movement_speed = 6
        self.fly_speed = 12
        self.acceleration = 40   # Units per second^2
        self.friction = 10       # Units per second^2 (on ground)
        self.air_control = 0.3   # Multiplier for air movement control
        
        # Mario-like baseline: higher jump, lighter gravity
        self.jump_height = 3.5
        self.gravity = -12.0 # Increased gravity for snappier fall
        self._physics_state = KinematicState(velocity_y=0.0, grounded=True)
        
        # Apply hot-config values if available
        if self._config:
            self._apply_config()
            self._config.on_change(self._on_config_change)
        
        # Lock mouse for first-person control
        mouse.locked = True
    
    def set_recorder(self, recorder: 'SessionRecorder') -> None:
        """Set the session recorder for input capture."""
        self._recorder = recorder
    
    def set_session_player(self, player: 'SessionPlayer') -> None:
        """Set the session player for replay."""
        self._session_player = player
    
    def _apply_config(self) -> None:
        """Apply all config values."""
        if not self._config:
            return
        self.mouse_sensitivity = self._config.get("mouse_sensitivity", 40.0)
        self.movement_speed = self._config.get("movement_speed", 6.0)
        self.fly_speed = self._config.get("fly_speed", 12.0)
        self.jump_height = self._config.get("jump_height", 3.5)
        self.gravity = self._config.get("gravity", -12.0)
        self.god_mode = self._config.get("god_mode", False)
    
    def _on_config_change(self, key: str, value) -> None:
        """Handle hot-config value change."""
        if key == "mouse_sensitivity":
            self.mouse_sensitivity = value
        elif key == "movement_speed":
            self.movement_speed = value
        elif key == "fly_speed":
            self.fly_speed = value
        elif key == "jump_height":
            self.jump_height = value
        elif key == "gravity":
            self.gravity = value
        elif key == "god_mode":
            self.god_mode = value
        
    def input(self, key):
        """Handle key press events"""
        # Record key event if recording
        if self._recorder and self._recorder.is_recording():
            pressed = not key.startswith('up_') and key not in ['scroll up', 'scroll down']
            clean_key = key.replace('up_', '') if not pressed else key
            self._recorder.record_key(clean_key, pressed)
        
        if key == 'space':
            # Record a jump request; actual jump will be performed in update()
            # based on coyote-time and buffering rules.
            register_jump_press(self._physics_state)
            
        # Toggle mouse lock with escape key
        if key == 'escape':
            mouse.locked = not mouse.locked
            
        # Toggle god mode with G (debug feature)
        # if key == 'g':
        #     self.god_mode = not self.god_mode
            
    def update(self, dt):
        """Update player movement and camera rotation every frame"""
        # Check for hot-config updates
        if self._config:
            self._config.update()
        
        # Record mouse movement if recording
        if self._recorder and self._recorder.is_recording():
            if mouse.velocity[0] != 0 or mouse.velocity[1] != 0:
                self._recorder.record_mouse_move(mouse.velocity[0], mouse.velocity[1])
        
        # Camera rotation with mouse
        if mouse.locked:
            # Horizontal rotation (yaw) - rotate player entity
            self.player.rotation_y += mouse.velocity[0] * self.mouse_sensitivity
            
            # Vertical rotation (pitch) - rotate camera pivot up/down
            if hasattr(self.player, 'camera_pivot'):
                self.player.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity
                # Clamp vertical rotation to prevent over-rotation
                self.player.camera_pivot.rotation_x = max(-89, min(89, self.player.camera_pivot.rotation_x))
        
        # Movement input
        forward_input = held_keys['w'] - held_keys['s']
        strafe_input = held_keys['d'] - held_keys['a']
        
        # Calculate movement direction based on player rotation
        # Calculate target velocity based on inputs
        target_velocity = Vec3(0, 0, 0)
        
        if forward_input != 0 or strafe_input != 0:
            # Forward movement (relative to player rotation)
            forward = Vec3(
                math.sin(math.radians(self.player.rotation_y)),
                0,
                math.cos(math.radians(self.player.rotation_y))
            ) * forward_input
            
            # Strafe movement (perpendicular to forward)
            right = Vec3(
                math.cos(math.radians(self.player.rotation_y)),
                0,
                -math.sin(math.radians(self.player.rotation_y))
            ) * strafe_input
            
            # Combine movement vectors
            move_dir = (forward + right).normalized()
            speed = self.fly_speed if self.god_mode else self.movement_speed
            target_velocity = move_dir * speed

        if self.god_mode:
            # GOD MODE / FLIGHT LOGIC
            # Vertical movement with Space (Up) and Shift (Down)
            vertical_input = held_keys['space'] - held_keys['shift']
            target_velocity.y = vertical_input * self.fly_speed
            
            # Simple direct movement for god mode (no inertia for precision)
            self.player.position += target_velocity * dt
            
            # Reset physics state so we don't carry momentum when toggling off
            self._physics_state.velocity_x = 0
            self._physics_state.velocity_y = 0
            self._physics_state.velocity_z = 0
            self._physics_state.grounded = False
            
        else:
            # NORMAL PHYSICS LOGIC
            
            # Apply acceleration/friction to approach target velocity
            # Different control in air vs ground
            control_factor = 1.0 if self._physics_state.grounded else self.air_control
            accel = self.acceleration * control_factor
            
            # Smoothly interpolate X velocity
            if target_velocity.x != 0:
                # Accelerating
                diff_x = target_velocity.x - self._physics_state.velocity_x
                change = accel * dt
                if abs(diff_x) < change:
                    self._physics_state.velocity_x = target_velocity.x
                else:
                    self._physics_state.velocity_x += math.copysign(change, diff_x)
            else:
                # Decelerating (Friction)
                fric = self.friction * dt * control_factor * 5 # Stronger stopping friction
                if abs(self._physics_state.velocity_x) < fric:
                    self._physics_state.velocity_x = 0
                else:
                    self._physics_state.velocity_x -= math.copysign(fric, self._physics_state.velocity_x)

            # Smoothly interpolate Z velocity
            if target_velocity.z != 0:
                # Accelerating
                diff_z = target_velocity.z - self._physics_state.velocity_z
                change = accel * dt
                if abs(diff_z) < change:
                    self._physics_state.velocity_z = target_velocity.z
                else:
                    self._physics_state.velocity_z += math.copysign(change, diff_z)
            else:
                # Decelerating (Friction)
                fric = self.friction * dt * control_factor * 5
                if abs(self._physics_state.velocity_z) < fric:
                    self._physics_state.velocity_z = 0
                else:
                    self._physics_state.velocity_z -= math.copysign(fric, self._physics_state.velocity_z)

            # Vertical physics: gravity and terrain-based ground using raycast
            apply_gravity(self._physics_state, dt, gravity=self.gravity, max_fall_speed=-30)

            def _ground_check(entity):
                # Use raycast to find the terrain height beneath the player.
                return raycast_ground_height(entity)

            def _wall_check(entity, movement):
                 # Check if moving in this direction would hit something
                 return raycast_wall_check(entity, movement, distance_buffer=0.5)

            integrate_movement(
                self.player,
                self._physics_state,
                dt,
                ground_check=_ground_check,
                wall_check=_wall_check
            )

            # Update coyote-time and jump-buffer timers now that grounded is up to date
            update_timers(self._physics_state, dt)

            # If we have a buffered jump and are within coyote time, perform the jump
            # Use generous Mario-like coyote and buffer windows
            if can_consume_jump(self._physics_state, coyote_time=0.2, jump_buffer_time=0.2):
                perform_jump(self._physics_state, self.jump_height)

            # Variable jump height: early release = short hop
            if self._physics_state.velocity_y > 0 and not held_keys['space']:
                self._physics_state.velocity_y *= 0.55