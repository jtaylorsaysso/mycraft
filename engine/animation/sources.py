"""Animation source wrappers for integrating with LayeredAnimator.

Provides adapters to make existing animation systems (AnimationController,
VoxelAnimator) compatible with the AnimationSource protocol.
"""

from typing import Dict
from panda3d.core import LVector3f

from engine.animation.core import Transform
from engine.animation.skeleton import Skeleton
from engine.animation.mannequin import AnimationController
from engine.animation.fsm import LocomotionFSM


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
        
        # Initialize FSM
        self.fsm = LocomotionFSM(self)
        self._current_anim = "idle"
        self._blend_time = 0.2
        self._anim_timer = 0.0
        self._playing = True
        self._looping = True
        self._duration = 1.0 # Default duration
        
    @property
    def current_clip(self):
        return self._current_anim
        
    @property
    def playing(self):
        return self._playing
        
    def play(self, anim_name, loop=True, blend_time=0.2):
        """Interface for FSM to trigger animations."""
        if self._current_anim != anim_name:
            self._current_anim = anim_name
            self._blend_time = blend_time
            self._looping = loop
            self._playing = True
            
            # Reset timer
            # Note: For procedural, resetting timer on change is good practice
            self._anim_timer = 0.0
            
            # Set duration estimates for procedural key-poses
            if anim_name == 'land':
                self._duration = 0.5
            elif anim_name == 'jump_start':
                self._duration = 0.3
            else:
                self._duration = 1.0

    def set_movement_state(self, velocity: LVector3f, grounded: bool):
        """Update movement state for procedural animations.
        
        Args:
            velocity: Current velocity vector
            grounded: Whether character is grounded
        """
        self._velocity = velocity
        self._grounded = grounded
        
        # Update FSM logic (transitions)
        # We pass a fixed small dt here because this is called from input/physics loop,
        # but the actual animation update happens in update().
        # However, for responsiveness, updating state here is good.
        self.fsm.update(0.016, velocity, grounded)
    
    def update(self, dt: float, skeleton: Skeleton) -> Dict[str, Transform]:
        """Update procedural animation and return transforms.
        
        Args:
            dt: Delta time
            skeleton: Skeleton to animate
            
        Returns:
            Bone transforms for procedural walk/idle
        """
        import math
        
        # Update FSM with real DT (advances logic if needed)
        self.fsm.update(dt, self._velocity, self._grounded)
        self._anim_timer += dt
        
        # Check for animation completion
        if not self._looping and self._playing:
            if self._anim_timer >= self._duration:
                self._playing = False
        
        transforms = {}
        
        # Helper to create transform that ADDS rotation to rest pose
        def make_transform(bone_name, rotation_offset):
            bone = skeleton.get_bone(bone_name)
            if not bone:
                return Transform(rotation=rotation_offset)
            pos = bone.rest_transform.position
            rest_rot = bone.rest_transform.rotation
            final_rot = LVector3f(
                rest_rot.x + rotation_offset.x,
                rest_rot.y + rotation_offset.y,
                rest_rot.z + rotation_offset.z
            )
            return Transform(position=pos, rotation=final_rot)

        # ---------------------------------------------------------------------
        # Procedural Generators based on self._current_anim (set by FSM)
        # ---------------------------------------------------------------------
        
        if self._current_anim == 'idle':
            # very subtle breathing
            sway = math.sin(self._anim_timer * 1.5) * 2.0
            transforms['upper_arm_right'] = make_transform('upper_arm_right', LVector3f(0, sway, 0))
            transforms['upper_arm_left'] = make_transform('upper_arm_left', LVector3f(0, sway, 0))
            # ensuring neutral legs
            transforms['thigh_right'] = make_transform('thigh_right', LVector3f(0, 0, 0))
            transforms['thigh_left'] = make_transform('thigh_left', LVector3f(0, 0, 0))
            
        elif self._current_anim in ['walk', 'run']:
            # Movement
            speed_factor = min(self._velocity.length() / 6.0, 1.5)
            # Use accumulated time for continuous phase
            phase = self._anim_timer * 10.0 * speed_factor
            
            arm_amp = 35.0 if self._current_anim == 'walk' else 50.0
            leg_amp = 30.0 if self._current_anim == 'walk' else 45.0
            
            arm_swing = math.sin(phase) * arm_amp
            leg_swing = math.sin(phase) * leg_amp
            
            transforms['upper_arm_right'] = make_transform('upper_arm_right', LVector3f(0, arm_swing, 0))
            transforms['upper_arm_left'] = make_transform('upper_arm_left', LVector3f(0, -arm_swing, 0))
            transforms['thigh_right'] = make_transform('thigh_right', LVector3f(0, -leg_swing, 0))
            transforms['thigh_left'] = make_transform('thigh_left', LVector3f(0, leg_swing, 0))
            
            if self._current_anim == 'run':
                transforms['chest'] = make_transform('chest', LVector3f(0, 10.0, 0)) # Lean
                
        elif self._current_anim == 'jump_start':
            # Static jump pose
            transforms['upper_arm_right'] = make_transform('upper_arm_right', LVector3f(0, -45, 0))
            transforms['upper_arm_left'] = make_transform('upper_arm_left', LVector3f(0, -45, 0))
            transforms['thigh_right'] = make_transform('thigh_right', LVector3f(0, 30, 0))
            transforms['thigh_left'] = make_transform('thigh_left', LVector3f(0, 30, 0))
            
        elif self._current_anim == 'fall_loop':
            # Flailing? Or just air pose.
            transforms['upper_arm_right'] = make_transform('upper_arm_right', LVector3f(0, -60, 0))
            transforms['upper_arm_left'] = make_transform('upper_arm_left', LVector3f(0, -60, 0))
            transforms['thigh_right'] = make_transform('thigh_right', LVector3f(0, 10, 0))
            transforms['thigh_left'] = make_transform('thigh_left', LVector3f(0, 10, 0))
            
        elif self._current_anim == 'land':
             # Crouch
            transforms['thigh_right'] = make_transform('thigh_right', LVector3f(0, -20, 0))
            transforms['thigh_left'] = make_transform('thigh_left', LVector3f(0, -20, 0))
        
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
