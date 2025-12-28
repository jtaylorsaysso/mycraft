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
            skeleton: Skeleton (not used by procedural system currently)
            
        Returns:
            Bone transforms (currently empty - controller modifies nodes directly)
        """
        # Update the controller's state machine and procedural animations
        self.controller.update(dt, self._velocity, self._grounded)
        
        # Note: AnimationController currently modifies NodePaths directly
        # rather than returning transforms. In a future refactor, we could
        # extract transforms from the mannequin's bone nodes here.
        # For now, return empty dict since controller handles its own application.
        return {}


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
