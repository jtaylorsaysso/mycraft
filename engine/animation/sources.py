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

        if is_walking:
            # Walking animation - procedural arm and leg swing
            # Advance walk phase
            if not hasattr(self, '_walk_phase'):
                self._walk_phase = 0.0
            
            speed_factor = min(horizontal_speed / 6.0, 1.5)
            self._walk_phase += dt * 10.0 * speed_factor  # 10.0 is walk frequency
            
            # Calculate swing angles
            phase = self._walk_phase
            arm_swing = math.sin(phase) * 35.0  # degrees
            leg_swing = math.sin(phase) * 30.0  # degrees
            
            # Arms swing opposite to legs
            transforms['upper_arm_right'] = make_transform('upper_arm_right', LVector3f(0, arm_swing, 0))
            transforms['upper_arm_left'] = make_transform('upper_arm_left', LVector3f(0, -arm_swing, 0))
            
            # Legs swing
            transforms['thigh_right'] = make_transform('thigh_right', LVector3f(0, -leg_swing, 0))
            transforms['thigh_left'] = make_transform('thigh_left', LVector3f(0, leg_swing, 0))
            
        else:
            # Idle animation - subtle breathing
            if not hasattr(self, '_idle_time'):
                self._idle_time = 0.0
            
            self._idle_time += dt
            
            # Very subtle arm sway
            sway = math.sin(self._idle_time * 1.5) * 2.0  # degrees
            transforms['upper_arm_right'] = make_transform('upper_arm_right', LVector3f(0, sway, 0))
            transforms['upper_arm_left'] = make_transform('upper_arm_left', LVector3f(0, sway, 0))
            
            # Legs at neutral position (explicitly set to ensure visibility)
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
