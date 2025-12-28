"""Animation source wrappers for integrating with LayeredAnimator.

Provides adapters to make existing animation systems (AnimationController,
VoxelAnimator) compatible with the AnimationSource protocol.
"""

from typing import Dict
from panda3d.core import LVector3f

from engine.animation.core import Transform
from engine.animation.skeleton import Skeleton
from engine.animation.mannequin import AnimationController


class ProceduralAnimationSource:
    """Wraps AnimationController as an AnimationSource for LayeredAnimator.
    
    This adapter allows the existing procedural animation system to work
    as a layer in the new layered animation architecture.
    """
    
    def __init__(self, controller: AnimationController):
        """Initialize wrapper.
        
        Args:
            controller: AnimationController to wrap
        """
        self.controller = controller
        self._velocity = LVector3f(0, 0, 0)
        self._grounded = True
    
    def set_movement_state(self, velocity: LVector3f, grounded: bool):
        """Update movement state for procedural animations.
        
        Args:
            velocity: Current velocity vector
            grounded: Whether character is grounded
        """
        self._velocity = velocity
        self._grounded = grounded
    
    def update(self, dt: float, skeleton: Skeleton) -> Dict[str, Transform]:
        """Update procedural animation and return transforms.
        
        Args:
            dt: Delta time
            skeleton: Skeleton to animate
            
        Returns:
            Bone transforms for procedural walk/idle
        """
        import math
        
        # Calculate horizontal speed
        horizontal_speed = math.sqrt(self._velocity.x ** 2 + self._velocity.y ** 2)
        
        # Determine if walking or idle
        is_walking = horizontal_speed > 0.5
        
        transforms = {}
        
        # Helper to create transform that ADDS rotation to rest pose
        # Animation provides rotation OFFSET, not absolute orientation
        def make_transform(bone_name, rotation_offset):
            bone = skeleton.get_bone(bone_name)
            if not bone:
                return Transform(rotation=rotation_offset)
            
            # Position: always use rest position (bone length)
            pos = bone.rest_transform.position
            
            # Rotation: ADD offset to rest rotation
            # Rest rotation defines bone direction (e.g., thigh pitch=90 to point down)
            # Animation offset modifies that (e.g., leg swing of ±30 degrees)
            rest_rot = bone.rest_transform.rotation
            final_rot = LVector3f(
                rest_rot.x + rotation_offset.x,
                rest_rot.y + rotation_offset.y,
                rest_rot.z + rotation_offset.z
            )
            return Transform(position=pos, rotation=final_rot)

        # Determine current animation state
        is_walking = horizontal_speed > 0.5
        
        # Transition blending
        if not hasattr(self, '_blend_state'):
            self._blend_state = 'idle'
            self._blend_timer = 0.0
            self._blend_duration = 0.2  # 200ms blend time
        
        target_state = 'walk' if is_walking else 'idle'
        
        # Update blend if state changed
        if target_state != self._blend_state:
            self._blend_timer = 0.0
            self._prev_state = self._blend_state
            self._blend_state = target_state
        
        # Advance blend timer
        if self._blend_timer < self._blend_duration:
            self._blend_timer = min(self._blend_timer + dt, self._blend_duration)
        
        # Calculate blend factor (0 = prev state, 1 = current state)
        blend_factor = self._blend_timer / self._blend_duration if self._blend_duration > 0 else 1.0

        # Determine speed tier
        # idle: < 0.5, walk: 0.5-6.0, run: 6.0-12.0, sprint: > 12.0
        if horizontal_speed < 0.5:
            speed_tier = 'idle'
        elif horizontal_speed < 6.0:
            speed_tier = 'walk'
        elif horizontal_speed < 12.0:
            speed_tier = 'run'
        else:
            speed_tier = 'sprint'
        
        # Check if in air (not grounded)
        is_airborne = not self._grounded
        
        if is_airborne:
            # Jump/Fall animations
            # Check vertical velocity to distinguish jump from fall
            # (We don't have direct access to velocity_z here, so use grounded state)
            # For now, use a simple airborne pose
            
            # Jump pose: arms up, legs tucked
            transforms['upper_arm_right'] = make_transform('upper_arm_right', LVector3f(0, -45, 0))
            transforms['upper_arm_left'] = make_transform('upper_arm_left', LVector3f(0, -45, 0))
            transforms['thigh_right'] = make_transform('thigh_right', LVector3f(0, 30, 0))
            transforms['thigh_left'] = make_transform('thigh_left', LVector3f(0, 30, 0))
            transforms['chest'] = make_transform('chest', LVector3f(0, 0, 0))
            
        elif speed_tier in ['walk', 'run', 'sprint']:
            # Movement animations with speed-based parameters
            # Advance walk phase
            if not hasattr(self, '_walk_phase'):
                self._walk_phase = 0.0
            
            # Speed-based parameters
            if speed_tier == 'walk':
                arm_amplitude = 35.0
                leg_amplitude = 30.0
                frequency_mult = 1.0
                torso_lean = 0.0
            elif speed_tier == 'run':
                arm_amplitude = 50.0
                leg_amplitude = 45.0
                frequency_mult = 1.3
                torso_lean = 10.0  # Lean forward
            else:  # sprint
                arm_amplitude = 60.0
                leg_amplitude = 55.0
                frequency_mult = 1.6
                torso_lean = 20.0  # Aggressive lean
            
            speed_factor = min(horizontal_speed / 6.0, 1.5)
            self._walk_phase += dt * 10.0 * speed_factor * frequency_mult
            
            # Calculate swing angles
            phase = self._walk_phase
            arm_swing = math.sin(phase) * arm_amplitude * blend_factor
            leg_swing = math.sin(phase) * leg_amplitude * blend_factor
            
            # Arms swing opposite to legs
            transforms['upper_arm_right'] = make_transform('upper_arm_right', LVector3f(0, arm_swing, 0))
            transforms['upper_arm_left'] = make_transform('upper_arm_left', LVector3f(0, -arm_swing, 0))
            
            # Legs swing
            transforms['thigh_right'] = make_transform('thigh_right', LVector3f(0, -leg_swing, 0))
            transforms['thigh_left'] = make_transform('thigh_left', LVector3f(0, leg_swing, 0))
            
            # Torso lean for run/sprint
            if torso_lean > 0:
                transforms['chest'] = make_transform('chest', LVector3f(0, torso_lean, 0))
            
        else:  # idle
            # Idle animation - subtle breathing
            if not hasattr(self, '_idle_time'):
                self._idle_time = 0.0
            
            self._idle_time += dt
            
            # Very subtle arm sway
            sway = math.sin(self._idle_time * 1.5) * 2.0 * blend_factor
            transforms['upper_arm_right'] = make_transform('upper_arm_right', LVector3f(0, sway, 0))
            transforms['upper_arm_left'] = make_transform('upper_arm_left', LVector3f(0, sway, 0))
            
            # Legs at neutral position
            transforms['thigh_right'] = make_transform('thigh_right', LVector3f(0, 0, 0))
            transforms['thigh_left'] = make_transform('thigh_left', LVector3f(0, 0, 0))
        
        return transforms


class KeyframeAnimationSource:
    """Wraps VoxelAnimator as an AnimationSource for LayeredAnimator.
    
    Allows keyframe animations to work as layers.
    """
    
    def __init__(self, animator):
        """Initialize wrapper.
        
        Args:
            animator: VoxelAnimator instance
        """
        self.animator = animator
    
    def update(self, dt: float, skeleton: Skeleton) -> Dict[str, Transform]:
        """Update keyframe animation and return transforms.
        
        Args:
            dt: Delta time
            skeleton: Skeleton to animate
            
        Returns:
            Bone transforms from current keyframe
        """
        # Update the animator
        self.animator.update(dt)
        
        # Get current pose from the animator
        if self.animator.current_clip and self.animator.playing:
            clip = self.animator.clips[self.animator.current_clip]
            return clip.get_pose(self.animator.current_time)
        
        return {}
