"""
Procedural Animation System for MyCraft

Provides AnimatedMannequin with hierarchical limb structure and AnimationController
for state-based animation management. Uses Ursina's animate() for smooth transitions.
"""

from enum import Enum, auto
from ursina import Entity, color, Vec3, time
import math
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from engine.core.hot_config import HotConfig


class AnimationState(Enum):
    """Player animation states."""
    IDLE = auto()
    WALKING = auto()
    JUMPING = auto()
    FALLING = auto()
    LANDING = auto()


class AnimatedMannequin(Entity):
    """
    A rigged mannequin with procedural animations.
    
    Body structure (7 parts):
    - Head
    - Torso
    - Right Arm (with shoulder pivot)
    - Left Arm (with shoulder pivot)
    - Right Leg (with hip pivot)
    - Left Leg (with hip pivot)
    
    Pivots allow limbs to rotate naturally from their attachment points.
    """
    
    def __init__(self, body_color=None, **kwargs):
        super().__init__(**kwargs)
        
        if body_color is None:
            body_color = color.rgb(150, 125, 100)
        self.body_color = body_color
        
        # Walk animation state
        self._walk_phase = 0.0
        self._idle_time = 0.0
        
        # Build the mannequin
        self._build_body()
    
    def _build_body(self):
        """Create all body parts with proper pivot points."""
        
        # Head - no pivot needed, sits on top
        self.head = Entity(
            parent=self,
            model='cube',
            color=self.body_color,
            scale=0.3,
            y=1.6
        )
        
        # Torso - central body
        self.torso = Entity(
            parent=self,
            model='cube',
            color=self.body_color,
            scale=(0.4, 0.6, 0.25),
            y=1.1
        )
        
        # === ARMS ===
        # Arms pivot from the shoulder (top of arm)
        # Using origin_y=0.5 means rotation happens at the top of the cube
        
        # Right Arm Pivot (at shoulder position)
        self.right_arm_pivot = Entity(
            parent=self,
            position=(0.28, 1.35, 0)
        )
        self.right_arm = Entity(
            parent=self.right_arm_pivot,
            model='cube',
            color=self.body_color,
            scale=(0.12, 0.5, 0.12),
            origin_y=0.5,  # Pivot at top (shoulder)
            y=0
        )
        
        # Left Arm Pivot
        self.left_arm_pivot = Entity(
            parent=self,
            position=(-0.28, 1.35, 0)
        )
        self.left_arm = Entity(
            parent=self.left_arm_pivot,
            model='cube',
            color=self.body_color,
            scale=(0.12, 0.5, 0.12),
            origin_y=0.5,
            y=0
        )
        
        # === LEGS ===
        # Legs pivot from the hip (top of leg)
        
        # Right Leg Pivot (at hip position)
        self.right_leg_pivot = Entity(
            parent=self,
            position=(0.1, 0.8, 0)
        )
        self.right_leg = Entity(
            parent=self.right_leg_pivot,
            model='cube',
            color=self.body_color,
            scale=(0.15, 0.5, 0.15),
            origin_y=0.5,  # Pivot at top (hip)
            y=0
        )
        
        # Left Leg Pivot
        self.left_leg_pivot = Entity(
            parent=self,
            position=(-0.1, 0.8, 0)
        )
        self.left_leg = Entity(
            parent=self.left_leg_pivot,
            model='cube',
            color=self.body_color,
            scale=(0.15, 0.5, 0.15),
            origin_y=0.5,
            y=0
        )
    
    def reset_pose(self):
        """Reset all limbs to neutral position."""
        self.right_arm_pivot.rotation_x = 0
        self.left_arm_pivot.rotation_x = 0
        self.right_leg_pivot.rotation_x = 0
        self.left_leg_pivot.rotation_x = 0
        self._walk_phase = 0.0


class AnimationController:
    """
    Controls animation state machine and procedural animations.
    
    Manages transitions between states and runs the appropriate
    procedural animation based on current state.
    """
    
    def __init__(self, mannequin: AnimatedMannequin, config: Optional['HotConfig'] = None):
        self.mannequin = mannequin
        self.config = config
        self._current_state = AnimationState.IDLE
        self._state_time = 0.0  # Time in current state
        self._landing_duration = 0.15  # Duration of landing animation
        
        # Animation parameters (tunable)
        self.walk_frequency = 10.0
        self.walk_amplitude_arms = 35.0
        self.walk_amplitude_legs = 30.0
        self.idle_bob_speed = 2.0
        self.idle_bob_amount = 0.01

        # Load from config if available
        if self.config:
            self._apply_config()
            self.config.on_change(self._on_config_change)

    def _apply_config(self):
        """Apply all animation config values."""
        self.walk_frequency = self.config.get("walk_frequency", 10.0)
        self.walk_amplitude_arms = self.config.get("walk_amplitude_arms", 35.0)
        self.walk_amplitude_legs = self.config.get("walk_amplitude_legs", 30.0)
        self.idle_bob_speed = self.config.get("idle_bob_speed", 2.0)
        self.idle_bob_amount = self.config.get("idle_bob_amount", 0.01)

    def _on_config_change(self, key: str, value):
        """Handle hot-config value change."""
        if key == "walk_frequency":
            self.walk_frequency = float(value)
        elif key == "walk_amplitude_arms":
            self.walk_amplitude_arms = float(value)
        elif key == "walk_amplitude_legs":
            self.walk_amplitude_legs = float(value)
        elif key == "idle_bob_speed":
            self.idle_bob_speed = float(value)
        elif key == "idle_bob_amount":
            self.idle_bob_amount = float(value)
    
    @property
    def current_state(self) -> AnimationState:
        return self._current_state
    
    def set_state(self, new_state: AnimationState):
        """Transition to a new animation state."""
        if new_state != self._current_state:
            self._on_exit_state(self._current_state)
            self._current_state = new_state
            self._state_time = 0.0
            self._on_enter_state(new_state)
    
    def _on_enter_state(self, state: AnimationState):
        """Called when entering a new state."""
        if state == AnimationState.IDLE:
            # Smoothly return to neutral pose
            self._animate_to_neutral(duration=0.2)
        
        elif state == AnimationState.JUMPING:
            # Arms go up and back
            self.mannequin.right_arm_pivot.animate('rotation_x', -60, duration=0.15)
            self.mannequin.left_arm_pivot.animate('rotation_x', -60, duration=0.15)
            # Legs tuck slightly
            self.mannequin.right_leg_pivot.animate('rotation_x', 15, duration=0.15)
            self.mannequin.left_leg_pivot.animate('rotation_x', 15, duration=0.15)
        
        elif state == AnimationState.FALLING:
            # Arms spread out
            self.mannequin.right_arm_pivot.animate('rotation_x', -30, duration=0.2)
            self.mannequin.left_arm_pivot.animate('rotation_x', -30, duration=0.2)
            # Legs dangle
            self.mannequin.right_leg_pivot.animate('rotation_x', 10, duration=0.2)
            self.mannequin.left_leg_pivot.animate('rotation_x', -10, duration=0.2)
        
        elif state == AnimationState.LANDING:
            # Quick crouch-like pose
            self.mannequin.right_arm_pivot.animate('rotation_x', 20, duration=0.08)
            self.mannequin.left_arm_pivot.animate('rotation_x', 20, duration=0.08)
            self.mannequin.right_leg_pivot.animate('rotation_x', -15, duration=0.08)
            self.mannequin.left_leg_pivot.animate('rotation_x', -15, duration=0.08)
    
    def _on_exit_state(self, state: AnimationState):
        """Called when leaving a state."""
        pass  # Currently no cleanup needed
    
    def _animate_to_neutral(self, duration: float = 0.2):
        """Smoothly animate all limbs to neutral position."""
        self.mannequin.right_arm_pivot.animate('rotation_x', 0, duration=duration)
        self.mannequin.left_arm_pivot.animate('rotation_x', 0, duration=duration)
        self.mannequin.right_leg_pivot.animate('rotation_x', 0, duration=duration)
        self.mannequin.left_leg_pivot.animate('rotation_x', 0, duration=duration)
    
    def update(self, dt: float, velocity: Vec3, grounded: bool):
        """
        Update animations based on movement state.
        
        Args:
            dt: Delta time since last frame
            velocity: Current velocity vector (world space)
            grounded: Whether the entity is on the ground
        """
        self._state_time += dt
        
        # Calculate horizontal speed (ignore Y for walk detection)
        horizontal_speed = math.sqrt(velocity.x ** 2 + velocity.z ** 2)
        
        # Determine appropriate state based on physics
        if self._current_state == AnimationState.LANDING:
            # Stay in landing until animation completes
            if self._state_time >= self._landing_duration:
                if horizontal_speed > 0.5:
                    self.set_state(AnimationState.WALKING)
                else:
                    self.set_state(AnimationState.IDLE)
        
        elif not grounded:
            if velocity.y > 0.5:
                self.set_state(AnimationState.JUMPING)
            elif velocity.y < -0.5:
                self.set_state(AnimationState.FALLING)
        
        else:
            # On ground
            was_airborne = self._current_state in (AnimationState.JUMPING, AnimationState.FALLING)
            
            if was_airborne:
                # Just landed
                self.set_state(AnimationState.LANDING)
            elif horizontal_speed > 0.5:
                self.set_state(AnimationState.WALKING)
            else:
                self.set_state(AnimationState.IDLE)
        
        # Run procedural animation for current state
        self._update_procedural_animation(dt, horizontal_speed)
    
    def _update_procedural_animation(self, dt: float, speed: float):
        """Run the procedural animation for the current state."""
        
        if self._current_state == AnimationState.WALKING:
            self._update_walk_animation(dt, speed)
        
        elif self._current_state == AnimationState.IDLE:
            self._update_idle_animation(dt)
        
        # JUMPING, FALLING, LANDING use pose-based animations set in _on_enter_state
    
    def _update_walk_animation(self, dt: float, speed: float):
        """Procedural walk cycle using sine-wave limb rotation."""
        # Advance walk phase based on speed
        # Faster movement = faster cycle
        speed_factor = min(speed / 6.0, 1.5)  # Cap at 1.5x normal speed
        self.mannequin._walk_phase += dt * self.walk_frequency * speed_factor
        
        # Calculate swing angles using sine wave
        phase = self.mannequin._walk_phase
        
        # Arm swing (opposite to legs for natural walking)
        arm_swing = math.sin(phase) * self.walk_amplitude_arms
        self.mannequin.right_arm_pivot.rotation_x = arm_swing
        self.mannequin.left_arm_pivot.rotation_x = -arm_swing
        
        # Leg swing (opposite arms)
        leg_swing = math.sin(phase) * self.walk_amplitude_legs
        self.mannequin.right_leg_pivot.rotation_x = -leg_swing
        self.mannequin.left_leg_pivot.rotation_x = leg_swing
    
    def _update_idle_animation(self, dt: float):
        """Subtle idle animation - gentle breathing/sway motion."""
        self.mannequin._idle_time += dt
        
        # Very subtle torso bob
        bob = math.sin(self.mannequin._idle_time * self.idle_bob_speed) * self.idle_bob_amount
        self.mannequin.torso.y = 1.1 + bob
        
        # Tiny arm sway (almost imperceptible)
        sway = math.sin(self.mannequin._idle_time * 1.5) * 2.0
        self.mannequin.right_arm_pivot.rotation_x = sway
        self.mannequin.left_arm_pivot.rotation_x = sway
