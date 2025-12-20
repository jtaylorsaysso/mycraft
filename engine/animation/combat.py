"""Combat-specific animation extensions with momentum and hit detection."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from panda3d.core import LVector3f
from engine.animation.core import AnimationClip, VoxelAnimator, Transform


@dataclass
class HitWindow:
    """Defines when an attack can deal damage."""
    start_time: float  # When hitbox becomes active
    end_time: float    # When hitbox deactivates
    damage_multiplier: float = 1.0  # Damage scaling for this window
    

@dataclass
class CombatClip(AnimationClip):
    """Animation clip with combat metadata."""
    hit_windows: List[HitWindow] = field(default_factory=list)
    can_cancel_after: float = 0.0  # Time when player can cancel into another action
    momentum_influence: float = 0.3  # How much movement affects the animation (0-1)
    recovery_time: float = 0.0  # Time after animation before next action
    

class CombatAnimator(VoxelAnimator):
    """Animator with combat-specific features.
    
    Extends VoxelAnimator with:
    - Hit detection windows
    - Momentum modulation
    - Cancel windows
    - Combo chaining
    """
    
    def __init__(self, rig, on_hit: Optional[Callable] = None):
        """Initialize combat animator.
        
        Args:
            rig: VoxelRig to animate
            on_hit: Callback when hit window is active (frame, damage_mult)
        """
        super().__init__(rig)
        self.on_hit = on_hit
        self.momentum: LVector3f = LVector3f(0, 0, 0)
        self.last_hit_check_time: float = -1.0
        self.can_cancel: bool = False
        
    def add_combat_clip(self, clip: CombatClip):
        """Add a combat animation clip."""
        self.clips[clip.name] = clip
    
    def set_momentum(self, velocity: LVector3f):
        """Set current movement momentum.
        
        Args:
            velocity: Current movement velocity
        """
        self.momentum = velocity
    
    def update(self, dt: float):
        """Update animation with combat features.
        
        Args:
            dt: Delta time
        """
        if not self.playing or not self.current_clip:
            return
        
        clip = self.clips[self.current_clip]
        
        # Check if this is a combat clip
        if isinstance(clip, CombatClip):
            # Check cancel window
            self.can_cancel = self.current_time >= clip.can_cancel_after
            
            # Check hit windows
            for hit_window in clip.hit_windows:
                if hit_window.start_time <= self.current_time <= hit_window.end_time:
                    # Only trigger once per window
                    if self.last_hit_check_time < hit_window.start_time:
                        if self.on_hit:
                            self.on_hit(self.current_time, hit_window.damage_multiplier)
                        self.last_hit_check_time = self.current_time
            
            # Apply momentum modulation
            if clip.momentum_influence > 0 and self.momentum.length() > 0.1:
                current_pose = clip.get_pose(self.current_time)
                
                # Modulate animation based on momentum
                # This is a simple example - you'd tune this per-animation
                momentum_factor = self.momentum.length() * clip.momentum_influence
                
                # Apply momentum to relevant bones (e.g., torso lean)
                if 'torso' in current_pose:
                    # Lean torso in direction of movement
                    lean_angle = momentum_factor * 10  # degrees
                    current_pose['torso'].rotation.y += lean_angle
        
        # Standard animation update
        super().update(dt)
    
    def can_cancel_current(self) -> bool:
        """Check if current animation can be cancelled.
        
        Returns:
            True if animation can be cancelled now
        """
        return self.can_cancel
    
    def try_combo(self, next_clip: str) -> bool:
        """Attempt to chain into next attack.
        
        Args:
            next_clip: Name of next combat clip
            
        Returns:
            True if combo was successful
        """
        if not self.can_cancel_current():
            return False
        
        self.play(next_clip, blend=True)
        return True


def create_walk_cycle(duration: float = 1.0) -> AnimationClip:
    """Create a basic walk cycle animation.
    
    Args:
        duration: Cycle duration in seconds
        
    Returns:
        Walk cycle AnimationClip
    """
    from engine.animation.core import Keyframe
    
    keyframes = [
        # Start: Right leg forward, left leg back
        Keyframe(
            time=0.0,
            transforms={
                'right_leg': Transform(rotation=LVector3f(25, 0, 0)),
                'left_leg': Transform(rotation=LVector3f(-25, 0, 0)),
                'right_arm': Transform(rotation=LVector3f(-30, 0, 0)),
                'left_arm': Transform(rotation=LVector3f(30, 0, 0)),
                'torso': Transform(position=LVector3f(0, 0, 0)),
            }
        ),
        # Mid: Legs passing
        Keyframe(
            time=duration / 2,
            transforms={
                'right_leg': Transform(rotation=LVector3f(-25, 0, 0)),
                'left_leg': Transform(rotation=LVector3f(25, 0, 0)),
                'right_arm': Transform(rotation=LVector3f(30, 0, 0)),
                'left_arm': Transform(rotation=LVector3f(-30, 0, 0)),
                'torso': Transform(position=LVector3f(0, 0, 0.05)),
            }
        ),
        # End: Back to start (loop)
        Keyframe(
            time=duration,
            transforms={
                'right_leg': Transform(rotation=LVector3f(25, 0, 0)),
                'left_leg': Transform(rotation=LVector3f(-25, 0, 0)),
                'right_arm': Transform(rotation=LVector3f(-30, 0, 0)),
                'left_arm': Transform(rotation=LVector3f(30, 0, 0)),
                'torso': Transform(position=LVector3f(0, 0, 0)),
            }
        ),
    ]
    
    return AnimationClip(
        name='walk',
        duration=duration,
        keyframes=keyframes,
        looping=True
    )


def create_sword_slash() -> CombatClip:
    """Create a basic sword slash attack.
    
    Returns:
        Sword slash CombatClip
    """
    from engine.animation.core import Keyframe
    
    keyframes = [
        # Windup
        Keyframe(
            time=0.0,
            transforms={
                'right_arm': Transform(rotation=LVector3f(0, -90, 0)),
                'torso': Transform(rotation=LVector3f(0, -20, 0)),
            }
        ),
        # Strike
        Keyframe(
            time=0.15,
            transforms={
                'right_arm': Transform(rotation=LVector3f(0, 90, 0)),
                'torso': Transform(rotation=LVector3f(0, 20, 0)),
            }
        ),
        # Follow-through
        Keyframe(
            time=0.3,
            transforms={
                'right_arm': Transform(rotation=LVector3f(0, 45, 0)),
                'torso': Transform(rotation=LVector3f(0, 10, 0)),
            }
        ),
        # Recovery
        Keyframe(
            time=0.5,
            transforms={
                'right_arm': Transform(rotation=LVector3f(0, 0, 0)),
                'torso': Transform(rotation=LVector3f(0, 0, 0)),
            }
        ),
    ]
    
    return CombatClip(
        name='sword_slash',
        duration=0.5,
        keyframes=keyframes,
        looping=False,
        hit_windows=[HitWindow(start_time=0.12, end_time=0.18, damage_multiplier=1.0)],
        can_cancel_after=0.35,
        momentum_influence=0.4,
        recovery_time=0.15
    )
