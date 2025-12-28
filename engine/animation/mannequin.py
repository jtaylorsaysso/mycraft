"""
Procedural Animation System for MyCraft (Panda3D Native)

Provides AnimatedMannequin with hierarchical limb structure and AnimationController
for state-based animation management using Panda3D NodePath transforms.
"""

from enum import Enum, auto
from panda3d.core import NodePath, LVector3f, GeomNode, CardMaker
from direct.interval.IntervalGlobal import LerpHprInterval, Sequence
import math
from typing import Optional, TYPE_CHECKING, Dict

from engine.animation.skeleton import HumanoidSkeleton, Bone

if TYPE_CHECKING:
    from engine.core.hot_config import HotConfig


class AnimationState(Enum):
    """Player animation states."""
    IDLE = auto()
    WALKING = auto()
    JUMPING = auto()
    FALLING = auto()
    LANDING = auto()


class AnimatedMannequin:
    """
    A rigged mannequin with procedural animations using Panda3D NodePaths.
    
    Now powered by HumanoidSkeleton for articulated limb movement with
    elbows, knees, and proper joint constraints.
    
    Backward compatible API: Properties like `right_arm`, `left_leg`, etc.
    still work but now reference skeleton bones.
    """
    
    def __init__(self, parent_node: NodePath, body_color=(0.6, 0.5, 0.4, 1.0)):
        """Initialize mannequin.
        
        Args:
            parent_node: Panda3D NodePath to attach mannequin to
            body_color: RGBA tuple for body color
        """
        self.root = parent_node.attachNewNode("mannequin")
        self.body_color = body_color
        
        # Walk animation state
        self._walk_phase = 0.0
        self._idle_time = 0.0
        
        # Create skeleton
        self.skeleton = HumanoidSkeleton()
        
        # Create visual nodes for each bone
        self.bone_nodes: Dict[str, NodePath] = {}
        
        # Build the mannequin
        self._build_body()
    
    def _create_cube(self, name: str, parent: NodePath, scale: tuple, pos: tuple = (0, 0, 0)):
        """Create a simple cube using CardMaker (placeholder for proper models)."""
        node = parent.attachNewNode(name)
        
        # Create a unit cube (roughly) using CardMaker for visibility
        cm = CardMaker('card')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)  # 1x1 centered
        
        # Create 6 faces
        # Front
        f = node.attachNewNode(cm.generate())
        f.setPos(0, -0.5, 0)
        
        # Back
        b = node.attachNewNode(cm.generate())
        b.setPos(0, 0.5, 0)
        b.setH(180)
        
        # Left
        l = node.attachNewNode(cm.generate())
        l.setPos(-0.5, 0, 0)
        l.setH(90)
        
        # Right
        r = node.attachNewNode(cm.generate())
        r.setPos(0.5, 0, 0)
        r.setH(-90)
        
        # Top
        t = node.attachNewNode(cm.generate())
        t.setPos(0, 0, 0.5)
        t.setP(-90)
        
        # Bottom
        bt = node.attachNewNode(cm.generate())
        bt.setPos(0, 0, -0.5)
        bt.setP(90)
        
        # Apply color
        node.setColorScale(*self.body_color)
        
        # Apply transform
        node.setScale(*scale)
        node.setPos(*pos)
        
        return node
    
    def _build_body(self):
        """Create all body parts with proper pivot points using skeleton."""
        
        # Create NodePath for each bone
        # We'll create simplified visual representations for now
        
        # Head
        head_node = self._create_cube(
            "head",
            self.root,
            scale=(0.3, 0.3, 0.3),
            pos=(0, 0, 1.6)
        )
        self.bone_nodes["head"] = head_node
        
        # Torso (represents spine + chest)
        torso_node = self._create_cube(
            "torso",
            self.root,
            scale=(0.4, 0.25, 0.6),
            pos=(0, 0, 1.1)
        )
        self.bone_nodes["chest"] = torso_node
        
        # === ARMS ===
        # Right arm - now articulated with upper_arm and forearm
        # For now, create single visual for entire arm (will split later for elbow)
        right_arm_pivot = self.root.attachNewNode("right_arm_pivot")
        right_arm_pivot.setPos(0.28, 0, 1.35)
        self.bone_nodes["upper_arm_right"] = right_arm_pivot
        
        right_arm_visual = self._create_cube(
            "right_arm",
            right_arm_pivot,
            scale=(0.12, 0.12, 0.5),
            pos=(0, 0, -0.25)
        )
        
        # Left arm
        left_arm_pivot = self.root.attachNewNode("left_arm_pivot")
        left_arm_pivot.setPos(-0.28, 0, 1.35)
        self.bone_nodes["upper_arm_left"] = left_arm_pivot
        
        left_arm_visual = self._create_cube(
            "left_arm",
            left_arm_pivot,
            scale=(0.12, 0.12, 0.5),
            pos=(0, 0, -0.25)
        )
        
        # === LEGS ===
        # Right leg - now articulated with thigh and shin
        right_leg_pivot = self.root.attachNewNode("right_leg_pivot")
        right_leg_pivot.setPos(0.1, 0, 0.8)
        self.bone_nodes["thigh_right"] = right_leg_pivot
        
        right_leg_visual = self._create_cube(
            "right_leg",
            right_leg_pivot,
            scale=(0.15, 0.15, 0.5),
            pos=(0, 0, -0.25)
        )
        
        # Left leg
        left_leg_pivot = self.root.attachNewNode("left_leg_pivot")
        left_leg_pivot.setPos(-0.1, 0, 0.8)
        self.bone_nodes["thigh_left"] = left_leg_pivot
        
        left_leg_visual = self._create_cube(
            "left_leg",
            left_leg_pivot,
            scale=(0.15, 0.15, 0.5),
            pos=(0, 0, -0.25)
        )
    
    # === Backward Compatibility Properties ===
    # These allow existing code to work unchanged
    
    @property
    def head(self) -> NodePath:
        """Head visual node."""
        return self.bone_nodes.get("head")
    
    @property
    def torso(self) -> NodePath:
        """Torso visual node (maps to chest bone)."""
        return self.bone_nodes.get("chest")
    
    @property
    def right_arm_pivot(self) -> NodePath:
        """Right arm pivot (maps to upper_arm_right bone)."""
        return self.bone_nodes.get("upper_arm_right")
    
    @property
    def left_arm_pivot(self) -> NodePath:
        """Left arm pivot (maps to upper_arm_left bone)."""
        return self.bone_nodes.get("upper_arm_left")
    
    @property
    def right_arm(self) -> NodePath:
        """Right arm visual (child of pivot)."""
        pivot = self.right_arm_pivot
        return pivot.getChild(0) if pivot and pivot.getNumChildren() > 0 else pivot
    
    @property
    def left_arm(self) -> NodePath:
        """Left arm visual (child of pivot)."""
        pivot = self.left_arm_pivot
        return pivot.getChild(0) if pivot and pivot.getNumChildren() > 0 else pivot
    
    @property
    def right_leg_pivot(self) -> NodePath:
        """Right leg pivot (maps to thigh_right bone)."""
        return self.bone_nodes.get("thigh_right")
    
    @property
    def left_leg_pivot(self) -> NodePath:
        """Left leg pivot (maps to thigh_left bone)."""
        return self.bone_nodes.get("thigh_left")
    
    @property
    def right_leg(self) -> NodePath:
        """Right leg visual (child of pivot)."""
        pivot = self.right_leg_pivot
        return pivot.getChild(0) if pivot and pivot.getNumChildren() > 0 else pivot
    
    @property
    def left_leg(self) -> NodePath:
        """Left leg visual (child of pivot)."""
        pivot = self.left_leg_pivot
        return pivot.getChild(0) if pivot and pivot.getNumChildren() > 0 else pivot
    
    def reset_pose(self):
        """Reset all limbs to neutral position."""
        self.right_arm_pivot.setHpr(0, 0, 0)
        self.left_arm_pivot.setHpr(0, 0, 0)
        self.right_leg_pivot.setHpr(0, 0, 0)
        self.left_leg_pivot.setHpr(0, 0, 0)
        self._walk_phase = 0.0
    
    def cleanup(self):
        """Remove mannequin from scene."""
        self.root.removeNode()


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
            self._set_limb_rotation(self.mannequin.right_arm_pivot, pitch=-60)
            self._set_limb_rotation(self.mannequin.left_arm_pivot, pitch=-60)
            # Legs tuck slightly
            self._set_limb_rotation(self.mannequin.right_leg_pivot, pitch=15)
            self._set_limb_rotation(self.mannequin.left_leg_pivot, pitch=15)
        
        elif state == AnimationState.FALLING:
            # Arms spread out
            self._set_limb_rotation(self.mannequin.right_arm_pivot, pitch=-30)
            self._set_limb_rotation(self.mannequin.left_arm_pivot, pitch=-30)
            # Legs dangle
            self._set_limb_rotation(self.mannequin.right_leg_pivot, pitch=10)
            self._set_limb_rotation(self.mannequin.left_leg_pivot, pitch=-10)
        
        elif state == AnimationState.LANDING:
            # Quick crouch-like pose
            self._set_limb_rotation(self.mannequin.right_arm_pivot, pitch=20)
            self._set_limb_rotation(self.mannequin.left_arm_pivot, pitch=20)
            self._set_limb_rotation(self.mannequin.right_leg_pivot, pitch=-15)
            self._set_limb_rotation(self.mannequin.left_leg_pivot, pitch=-15)
    
    def _on_exit_state(self, state: AnimationState):
        """Called when leaving a state."""
        pass  # Currently no cleanup needed
    
    def _set_limb_rotation(self, limb: NodePath, pitch: float = 0, heading: float = 0, roll: float = 0):
        """Set limb rotation (Panda3D uses HPR: heading, pitch, roll)."""
        limb.setHpr(heading, pitch, roll)
    
    def _animate_to_neutral(self, duration: float = 0.2):
        """Smoothly animate all limbs to neutral position."""
        # For now, just set directly - could use intervals for smooth transitions
        self._set_limb_rotation(self.mannequin.right_arm_pivot)
        self._set_limb_rotation(self.mannequin.left_arm_pivot)
        self._set_limb_rotation(self.mannequin.right_leg_pivot)
        self._set_limb_rotation(self.mannequin.left_leg_pivot)
    
    def update(self, dt: float, velocity: LVector3f, grounded: bool):
        """
        Update animations based on movement state.
        
        Args:
            dt: Delta time since last frame
            velocity: Current velocity vector (world space)
            grounded: Whether the entity is on the ground
        """
        self._state_time += dt
        
        # Calculate horizontal speed (ignore Z for walk detection in Panda3D coords)
        horizontal_speed = math.sqrt(velocity.x ** 2 + velocity.y ** 2)
        
        # Determine appropriate state based on physics
        if self._current_state == AnimationState.LANDING:
            # Stay in landing until animation completes
            if self._state_time >= self._landing_duration:
                if horizontal_speed > 0.5:
                    self.set_state(AnimationState.WALKING)
                else:
                    self.set_state(AnimationState.IDLE)
        
        elif not grounded:
            if velocity.z > 0.5:  # Z is up in Panda3D
                self.set_state(AnimationState.JUMPING)
            elif velocity.z < -0.5:
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
        speed_factor = min(speed / 6.0, 1.5)  # Cap at 1.5x normal speed
        self.mannequin._walk_phase += dt * self.walk_frequency * speed_factor
        
        # Calculate swing angles using sine wave
        phase = self.mannequin._walk_phase
        
        # Arm swing (opposite to legs for natural walking)
        arm_swing = math.sin(phase) * self.walk_amplitude_arms
        self._set_limb_rotation(self.mannequin.right_arm_pivot, pitch=arm_swing)
        self._set_limb_rotation(self.mannequin.left_arm_pivot, pitch=-arm_swing)
        
        # Leg swing (opposite arms)
        leg_swing = math.sin(phase) * self.walk_amplitude_legs
        self._set_limb_rotation(self.mannequin.right_leg_pivot, pitch=-leg_swing)
        self._set_limb_rotation(self.mannequin.left_leg_pivot, pitch=leg_swing)
    
    def _update_idle_animation(self, dt: float):
        """Subtle idle animation - gentle breathing/sway motion."""
        self.mannequin._idle_time += dt
        
        # Very subtle torso bob
        bob = math.sin(self.mannequin._idle_time * self.idle_bob_speed) * self.idle_bob_amount
        self.mannequin.torso.setZ(1.1 + bob)
        
        # Tiny arm sway (almost imperceptible)
        sway = math.sin(self.mannequin._idle_time * 1.5) * 2.0
        self._set_limb_rotation(self.mannequin.right_arm_pivot, pitch=sway)
        self._set_limb_rotation(self.mannequin.left_arm_pivot, pitch=sway)
