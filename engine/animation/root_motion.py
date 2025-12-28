"""Root motion system for animation-driven character movement.

Enables attacks and other animations to physically move the character,
creating commitment-based combat where attacks drive forward momentum.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from panda3d.core import LVector3f
import math

from engine.animation.core import AnimationClip, Keyframe, Transform


@dataclass
class RootMotionCurve:
    """Defines how root motion changes over time.
    
    Root motion curves describe the character's displacement during
    an animation (e.g., lunging forward during an attack).
    """
    
    # List of (time, delta_position) samples
    samples: List[Tuple[float, LVector3f]] = field(default_factory=list)
    
    def add_sample(self, time: float, delta: LVector3f):
        """Add a motion sample at a specific time.
        
        Args:
            time: Time in animation (seconds)
            delta: Position delta from previous sample
        """
        self.samples.append((time, delta))
        # Keep sorted by time
        self.samples.sort(key=lambda x: x[0])
    
    def get_delta(self, start_time: float, end_time: float) -> LVector3f:
        """Get accumulated motion delta between two times.
        
        Args:
            start_time: Start time (seconds)
            end_time: End time (seconds)
            
        Returns:
            Total displacement vector
        """
        if not self.samples:
            return LVector3f(0, 0, 0)
        
        total_delta = LVector3f(0, 0, 0)
        
        for i, (sample_time, delta) in enumerate(self.samples):
            # Skip samples before start_time
            if sample_time < start_time:
                continue
            # Stop at samples after end_time
            if sample_time > end_time:
                break
            
            # Accumulate delta
            total_delta += delta
        
        return total_delta
    
    def get_velocity_at(self, time: float) -> LVector3f:
        """Get instantaneous velocity at a specific time.
        
        Args:
            time: Time in animation (seconds)
            
        Returns:
            Velocity vector (units/second)
        """
        if not self.samples or len(self.samples) < 2:
            return LVector3f(0, 0, 0)
        
        # Find surrounding samples
        prev_sample = self.samples[0]
        next_sample = self.samples[-1]
        
        for i in range(len(self.samples) - 1):
            if self.samples[i][0] <= time <= self.samples[i + 1][0]:
                prev_sample = self.samples[i]
                next_sample = self.samples[i + 1]
                break
        
        # Calculate velocity between samples
        time_diff = next_sample[0] - prev_sample[0]
        if time_diff > 0:
            return next_sample[1] / time_diff
        
        return LVector3f(0, 0, 0)
    
    @classmethod
    def linear(cls, total_displacement: LVector3f, duration: float, samples: int = 10) -> 'RootMotionCurve':
        """Create a linear root motion curve.
        
        Args:
            total_displacement: Total movement over animation
            duration: Animation duration
            samples: Number of samples to generate
            
        Returns:
            Root motion curve with linear movement
        """
        curve = cls()
        delta_per_sample = total_displacement / samples
        
        for i in range(samples):
            time = (i / samples) * duration
            curve.add_sample(time, delta_per_sample)
        
        return curve
    
    @classmethod
    def ease_in_out(cls, total_displacement: LVector3f, duration: float, samples: int = 20) -> 'RootMotionCurve':
        """Create an ease-in-out root motion curve.
        
        Starts slow, accelerates, then decelerates at the end.
        
        Args:
            total_displacement: Total movement over animation
            duration: Animation duration
            samples: Number of samples to generate
            
        Returns:
            Root motion curve with eased movement
        """
        curve = cls()
        
        for i in range(samples):
            t = i / samples
            # Ease-in-out formula
            eased_t = t * t * (3.0 - 2.0 * t)
            
            # Calculate delta for this segment
            if i == 0:
                prev_eased = 0.0
            else:
                prev_t = (i - 1) / samples
                prev_eased = prev_t * prev_t * (3.0 - 2.0 * prev_t)
            
            delta = total_displacement * (eased_t - prev_eased)
            time = t * duration
            curve.add_sample(time, delta)
        
        return curve
    
    @classmethod
    def attack_lunge(cls, forward_distance: float, duration: float) -> 'RootMotionCurve':
        """Create a typical attack lunge curve.
        
        Fast acceleration during windup, peak speed during strike,
        deceleration during recovery.
        
        Args:
            forward_distance: Total forward movement
            duration: Attack duration
            
        Returns:
            Root motion curve for attack lunge
        """
        curve = cls()
        samples = 15
        
        for i in range(samples):
            t = i / samples
            
            # Custom curve: slow start, fast middle, slow end
            # Using a modified sine wave
            progress = (1.0 - math.cos(t * math.pi)) / 2.0
            
            if i == 0:
                prev_progress = 0.0
            else:
                prev_t = (i - 1) / samples
                prev_progress = (1.0 - math.cos(prev_t * math.pi)) / 2.0
            
            delta_progress = progress - prev_progress
            delta = LVector3f(0, forward_distance * delta_progress, 0)  # Y is forward in Panda3D
            time = t * duration
            curve.add_sample(time, delta)
        
        return curve


@dataclass
class RootMotionClip(AnimationClip):
    """Animation clip with root motion data.
    
    Extends AnimationClip to include character displacement information,
    enabling animation-driven movement.
    """
    
    root_motion: Optional[RootMotionCurve] = None
    
    def get_root_delta(self, start_time: float, end_time: float) -> LVector3f:
        """Get root motion delta between two times.
        
        Args:
            start_time: Start time
            end_time: End time
            
        Returns:
            Displacement vector
        """
        if self.root_motion:
            return self.root_motion.get_delta(start_time, end_time)
        return LVector3f(0, 0, 0)


class RootMotionApplicator:
    """Applies root motion from animations to character physics.
    
    Extracts motion deltas from playing animations and applies them
    to the character's kinematic state, enabling animation-driven movement.
    """
    
    def __init__(self):
        """Initialize root motion applicator."""
        self.enabled = True
        self.scale = 1.0  # Global scale for root motion
        self._last_time: Dict[str, float] = {}  # Track last time per clip
    
    def extract_and_apply(
        self,
        clip: RootMotionClip,
        current_time: float,
        dt: float,
        kinematic_state,
        character_rotation: float = 0.0
    ) -> LVector3f:
        """Extract root motion and apply to kinematic state.
        
        Args:
            clip: Animation clip with root motion
            current_time: Current time in animation
            dt: Delta time since last frame
            kinematic_state: Character's kinematic state
            character_rotation: Character's heading (degrees)
            
        Returns:
            Applied displacement vector (world space)
        """
        if not self.enabled or not clip.root_motion:
            return LVector3f(0, 0, 0)
        
        # Get last time for this clip
        clip_id = id(clip)
        last_time = self._last_time.get(clip_id, current_time - dt)
        
        # Extract delta from animation
        delta_local = clip.get_root_delta(last_time, current_time)
        
        # Scale delta
        delta_local *= self.scale
        
        # Rotate delta to world space based on character rotation
        # Panda3D uses heading (H) for Y-axis rotation
        heading_rad = math.radians(character_rotation)
        cos_h = math.cos(heading_rad)
        sin_h = math.sin(heading_rad)
        
        # Rotate vector (Y-forward, X-right in Panda3D)
        delta_world = LVector3f(
            delta_local.x * cos_h - delta_local.y * sin_h,
            delta_local.x * sin_h + delta_local.y * cos_h,
            delta_local.z
        )
        
        # Apply to kinematic state
        if hasattr(kinematic_state, 'position'):
            kinematic_state.position += delta_world
        elif hasattr(kinematic_state, 'pos'):
            kinematic_state.pos += delta_world
        
        # Update last time
        self._last_time[clip_id] = current_time
        
        return delta_world
    
    def reset_clip(self, clip: RootMotionClip):
        """Reset tracking for a clip (call when clip starts/stops).
        
        Args:
            clip: Clip to reset
        """
        clip_id = id(clip)
        if clip_id in self._last_time:
            del self._last_time[clip_id]
    
    def set_enabled(self, enabled: bool):
        """Enable or disable root motion application.
        
        Args:
            enabled: Whether root motion is enabled
        """
        self.enabled = enabled
    
    def set_scale(self, scale: float):
        """Set global root motion scale.
        
        Args:
            scale: Scale factor (1.0 = normal, 0.5 = half speed, etc.)
        """
        self.scale = max(0.0, scale)


# Helper function to add root motion to existing combat clips
def add_root_motion_to_attack(
    clip: AnimationClip,
    forward_distance: float = 1.5,
    motion_type: str = "lunge"
) -> RootMotionClip:
    """Convert a regular AnimationClip to RootMotionClip with motion.
    
    Args:
        clip: Original animation clip
        forward_distance: How far to move forward (voxel units)
        motion_type: Type of motion curve ("lunge", "linear", "ease")
        
    Returns:
        New RootMotionClip with root motion
    """
    # Create root motion curve based on type
    if motion_type == "lunge":
        curve = RootMotionCurve.attack_lunge(forward_distance, clip.duration)
    elif motion_type == "linear":
        curve = RootMotionCurve.linear(
            LVector3f(0, forward_distance, 0),
            clip.duration
        )
    elif motion_type == "ease":
        curve = RootMotionCurve.ease_in_out(
            LVector3f(0, forward_distance, 0),
            clip.duration
        )
    else:
        curve = RootMotionCurve.attack_lunge(forward_distance, clip.duration)
    
    # Create new RootMotionClip with same data
    return RootMotionClip(
        name=clip.name,
        duration=clip.duration,
        keyframes=clip.keyframes,
        looping=clip.looping,
        root_motion=curve
    )
