"""Combat animation source for layered animation system.

Provides combat-specific animation clips (attacks, dodge, parry) that can be
layered on top of locomotion animations.
"""

from typing import Dict, Optional
from panda3d.core import LVector3f

from engine.animation.core import Transform, Keyframe, AnimationClip
from engine.animation.combat import CombatClip, HitWindow, create_sword_slash
from engine.animation.root_motion import RootMotionCurve
from engine.animation.skeleton import Skeleton


class CombatAnimationSource:
    """Animation source for combat actions (attacks, dodge, parry).
    
    Manages combat animation clips and provides them to the layered animator.
    Supports triggering specific animations based on combat state.
    """
    
    def __init__(self):
        """Initialize combat animation source."""
        self.clips: Dict[str, CombatClip] = {}
        self.current_clip: Optional[str] = None
        self.current_time: float = 0.0
        self.playing: bool = False
        
        # Create combat animation clips
        self._create_clips()
    
    def _create_clips(self):
        """Create all combat animation clips."""
        # Attack animation
        self.clips["sword_slash"] = create_sword_slash()
        
        # Dodge animation (quick sidestep)
        self.clips["dodge"] = self._create_dodge_animation()
        
        # Parry animations
        self.clips["parry_start"] = self._create_parry_start()
        self.clips["parry_success"] = self._create_parry_success()
        self.clips["parry_fail"] = self._create_parry_fail()
    
    def _create_dodge_animation(self) -> CombatClip:
        """Create dodge step animation.
        
        Quick directional sidestep (0.3s) with 3.0 unit displacement.
        Uses root motion for movement.
        
        Returns:
            Dodge animation clip
        """
        keyframes = [
            # Start: crouch slightly
            Keyframe(
                time=0.0,
                transforms={
                    'hips': Transform(position=LVector3f(0, 0, -0.1)),
                    'chest': Transform(rotation=LVector3f(0, 10, 0)),
                }
            ),
            # Mid: lean into dodge direction
            Keyframe(
                time=0.15,
                transforms={
                    'hips': Transform(position=LVector3f(0, 0, -0.05)),
                    'chest': Transform(rotation=LVector3f(0, 15, 0)),
                    'upper_arm_right': Transform(rotation=LVector3f(0, -20, 0)),
                    'upper_arm_left': Transform(rotation=LVector3f(0, 20, 0)),
                }
            ),
            # End: recover to neutral
            Keyframe(
                time=0.3,
                transforms={
                    'hips': Transform(position=LVector3f(0, 0, 0)),
                    'chest': Transform(rotation=LVector3f(0, 0, 0)),
                    'upper_arm_right': Transform(rotation=LVector3f(0, 0, 0)),
                    'upper_arm_left': Transform(rotation=LVector3f(0, 0, 0)),
                }
            ),
        ]
        
        # Root motion: 3.0 unit displacement over 0.3s
        # Direction will be applied when playing based on input
        root_motion = RootMotionCurve.ease_in_out(
            total_displacement=LVector3f(0, 3.0, 0),  # Forward by default
            duration=0.3,
            samples=10
        )
        
        return CombatClip(
            name='dodge',
            duration=0.3,
            keyframes=keyframes,
            looping=False,
            root_motion=root_motion,
            can_cancel_after=0.3,  # Can't cancel dodge
            momentum_influence=0.0  # Dodge is animation-driven, not momentum-based
        )
    
    def _create_parry_start(self) -> AnimationClip:
        """Create parry start animation (defensive stance).
        
        Returns:
            Parry start animation clip
        """
        keyframes = [
            # Neutral
            Keyframe(
                time=0.0,
                transforms={
                    'upper_arm_right': Transform(rotation=LVector3f(0, 0, 0)),
                    'upper_arm_left': Transform(rotation=LVector3f(0, 0, 0)),
                    'chest': Transform(rotation=LVector3f(0, 0, 0)),
                }
            ),
            # Defensive stance
            Keyframe(
                time=0.2,
                transforms={
                    'upper_arm_right': Transform(rotation=LVector3f(-45, -30, 0)),
                    'upper_arm_left': Transform(rotation=LVector3f(-45, 30, 0)),
                    'chest': Transform(rotation=LVector3f(0, -5, 0)),
                }
            ),
        ]
        
        return AnimationClip(
            name='parry_start',
            duration=0.2,
            keyframes=keyframes,
            looping=False
        )
    
    def _create_parry_success(self) -> AnimationClip:
        """Create parry success animation (counter-ready).
        
        Returns:
            Parry success animation clip
        """
        keyframes = [
            # Defensive stance
            Keyframe(
                time=0.0,
                transforms={
                    'upper_arm_right': Transform(rotation=LVector3f(-45, -30, 0)),
                    'upper_arm_left': Transform(rotation=LVector3f(-45, 30, 0)),
                    'chest': Transform(rotation=LVector3f(0, -5, 0)),
                }
            ),
            # Counter-ready (slight recoil then forward)
            Keyframe(
                time=0.15,
                transforms={
                    'upper_arm_right': Transform(rotation=LVector3f(-30, -45, 0)),
                    'upper_arm_left': Transform(rotation=LVector3f(-30, 45, 0)),
                    'chest': Transform(rotation=LVector3f(0, 5, 0)),
                }
            ),
            # Return to neutral
            Keyframe(
                time=0.3,
                transforms={
                    'upper_arm_right': Transform(rotation=LVector3f(0, 0, 0)),
                    'upper_arm_left': Transform(rotation=LVector3f(0, 0, 0)),
                    'chest': Transform(rotation=LVector3f(0, 0, 0)),
                }
            ),
        ]
        
        return AnimationClip(
            name='parry_success',
            duration=0.3,
            keyframes=keyframes,
            looping=False
        )
    
    def _create_parry_fail(self) -> AnimationClip:
        """Create parry fail animation (stagger).
        
        Returns:
            Parry fail animation clip
        """
        keyframes = [
            # Defensive stance
            Keyframe(
                time=0.0,
                transforms={
                    'upper_arm_right': Transform(rotation=LVector3f(-45, -30, 0)),
                    'upper_arm_left': Transform(rotation=LVector3f(-45, 30, 0)),
                    'chest': Transform(rotation=LVector3f(0, -5, 0)),
                }
            ),
            # Stagger back
            Keyframe(
                time=0.2,
                transforms={
                    'upper_arm_right': Transform(rotation=LVector3f(-60, -45, 0)),
                    'upper_arm_left': Transform(rotation=LVector3f(-60, 45, 0)),
                    'chest': Transform(rotation=LVector3f(0, -15, 0)),
                    'hips': Transform(position=LVector3f(0, 0, -0.1)),
                }
            ),
            # Recover
            Keyframe(
                time=0.5,
                transforms={
                    'upper_arm_right': Transform(rotation=LVector3f(0, 0, 0)),
                    'upper_arm_left': Transform(rotation=LVector3f(0, 0, 0)),
                    'chest': Transform(rotation=LVector3f(0, 0, 0)),
                    'hips': Transform(position=LVector3f(0, 0, 0)),
                }
            ),
        ]
        
        return AnimationClip(
            name='parry_fail',
            duration=0.5,
            keyframes=keyframes,
            looping=False
        )
    
    def play(self, clip_name: str):
        """Play a combat animation clip.
        
        Args:
            clip_name: Name of clip to play
        """
        if clip_name in self.clips:
            self.current_clip = clip_name
            self.current_time = 0.0
            self.playing = True
    
    def stop(self):
        """Stop current animation."""
        self.playing = False
        self.current_clip = None
        self.current_time = 0.0
    
    def update(self, dt: float, skeleton: Skeleton) -> Dict[str, Transform]:
        """Update combat animation and return transforms.
        
        Args:
            dt: Delta time
            skeleton: Skeleton to animate
            
        Returns:
            Bone transforms from current animation
        """
        if not self.playing or not self.current_clip:
            return {}
        
        # Update time
        self.current_time += dt
        
        # Get current clip
        clip = self.clips[self.current_clip]
        
        # Check if animation finished
        if self.current_time >= clip.duration:
            self.stop()
            return {}
        
        # Get pose at current time
        pose = clip.get_pose(self.current_time)
        
        # Patch pose with skeletal constraints (prevent limb collapse)
        # We assume clips define rotations (absolute) and hip adjustments (delta)
        # but don't define structural bone lengths.
        final_pose = {}
        for bone_name, transform in pose.items():
            bone = skeleton.get_bone(bone_name)
            if not bone:
                continue
                
            rest_pos = bone.rest_transform.position
            rest_rot = bone.rest_transform.rotation
            
            # Rotation: ADD clip rotation offset to rest rotation
            # Clip provides animation offset (e.g., arm swing), not absolute orientation
            final_rot = LVector3f(
                rest_rot.x + transform.rotation.x,
                rest_rot.y + transform.rotation.y,
                rest_rot.z + transform.rotation.z
            )
            
            # Create new transform to avoid mutating cached keyframe data
            new_transform = Transform(
                rotation=final_rot,
                scale=transform.scale
            )
            
            if bone_name == 'hips':
                # For hips, treat animating position as DELTA from rest height
                # dodge used Z=-0.1, so we want 2.1 + (-0.1) = 2.0
                new_transform.position = rest_pos + transform.position
            else:
                # For all other bones, enforce fixed bone length (rest position)
                new_transform.position = rest_pos
                
            final_pose[bone_name] = new_transform
            
        return final_pose
    
    def get_current_clip(self) -> Optional[CombatClip]:
        """Get currently playing clip.
        
        Returns:
            Current combat clip or None
        """
        if self.current_clip and self.current_clip in self.clips:
            return self.clips[self.current_clip]
        return None
    
    def is_playing(self) -> bool:
        """Check if an animation is currently playing.
        
        Returns:
            True if playing
        """
        return self.playing
