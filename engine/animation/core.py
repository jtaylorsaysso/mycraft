"""Voxel animation system for Panda3D.

Hybrid keyframe + procedural animation system designed for pure-voxel characters.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from panda3d.core import NodePath, LVector3f, LQuaternionf
import math


@dataclass
class Transform:
    """3D transform (position, rotation, scale)."""
    position: LVector3f = field(default_factory=lambda: LVector3f(0, 0, 0))
    rotation: LVector3f = field(default_factory=lambda: LVector3f(0, 0, 0))  # Euler angles (HPR)
    scale: LVector3f = field(default_factory=lambda: LVector3f(1, 1, 1))
    
    def apply_to_node(self, node: NodePath):
        """Apply this transform to a Panda3D NodePath."""
        node.setPos(self.position)
        node.setHpr(self.rotation)
        node.setScale(self.scale)
    
    def lerp(self, other: 'Transform', t: float) -> 'Transform':
        """Linear interpolation between transforms."""
        return Transform(
            position=self.position + (other.position - self.position) * t,
            rotation=self.rotation + (other.rotation - self.rotation) * t,
            scale=self.scale + (other.scale - self.scale) * t
        )


@dataclass
class Keyframe:
    """Single keyframe in an animation."""
    time: float  # Time in seconds
    transforms: Dict[str, Transform]  # Bone name -> Transform
    
    
@dataclass
class AnimationClip:
    """Keyframe animation data."""
    name: str
    duration: float
    keyframes: List[Keyframe]
    looping: bool = True
    
    def get_pose(self, time: float) -> Dict[str, Transform]:
        """Get interpolated pose at given time.
        
        Args:
            time: Time in seconds (will wrap if looping)
            
        Returns:
            Dictionary of bone name -> Transform
        """
        if self.looping:
            time = time % self.duration
        else:
            time = min(time, self.duration)
        
        # Find surrounding keyframes
        prev_kf = self.keyframes[0]
        next_kf = self.keyframes[-1]
        
        for i, kf in enumerate(self.keyframes):
            if kf.time <= time:
                prev_kf = kf
                if i + 1 < len(self.keyframes):
                    next_kf = self.keyframes[i + 1]
                else:
                    next_kf = self.keyframes[0] if self.looping else kf
        
        # Interpolate between keyframes
        if prev_kf.time == next_kf.time:
            return prev_kf.transforms.copy()
        
        t = (time - prev_kf.time) / (next_kf.time - prev_kf.time)
        
        result = {}
        for bone_name in prev_kf.transforms:
            if bone_name in next_kf.transforms:
                result[bone_name] = prev_kf.transforms[bone_name].lerp(
                    next_kf.transforms[bone_name], t
                )
            else:
                result[bone_name] = prev_kf.transforms[bone_name]
        
        return result


class VoxelRig:
    """Hierarchical voxel character rig.
    
    Represents a character as a hierarchy of voxel body parts (bones).
    Each bone is a Panda3D NodePath that can be transformed.
    """
    
    def __init__(self, root: NodePath):
        """Initialize rig.
        
        Args:
            root: Root NodePath for the character
        """
        self.root = root
        self.bones: Dict[str, NodePath] = {}
        self.bone_hierarchy: Dict[str, str] = {}  # child -> parent
        
    def add_bone(self, name: str, parent_name: Optional[str] = None) -> NodePath:
        """Add a bone to the rig.
        
        Args:
            name: Bone name (e.g., 'torso', 'right_arm')
            parent_name: Parent bone name (None for root bones)
            
        Returns:
            NodePath for the new bone
        """
        if parent_name and parent_name in self.bones:
            parent = self.bones[parent_name]
        else:
            parent = self.root
        
        bone = parent.attachNewNode(name)
        self.bones[name] = bone
        
        if parent_name:
            self.bone_hierarchy[name] = parent_name
        
        return bone
    
    def get_bone(self, name: str) -> Optional[NodePath]:
        """Get bone by name."""
        return self.bones.get(name)
    
    def apply_pose(self, pose: Dict[str, Transform]):
        """Apply a pose to the rig.
        
        Args:
            pose: Dictionary of bone name -> Transform
        """
        for bone_name, transform in pose.items():
            if bone_name in self.bones:
                transform.apply_to_node(self.bones[bone_name])


class VoxelAnimator:
    """Animates a VoxelRig using AnimationClips."""
    
    def __init__(self, rig: VoxelRig):
        """Initialize animator.
        
        Args:
            rig: VoxelRig to animate
        """
        self.rig = rig
        self.clips: Dict[str, AnimationClip] = {}
        self.current_clip: Optional[str] = None
        self.current_time: float = 0.0
        self.playing: bool = False
        self.blend_time: float = 0.2  # Seconds to blend between animations
        self.blend_progress: float = 1.0  # 1.0 = fully in current animation
        self.previous_pose: Optional[Dict[str, Transform]] = None
        
    def add_clip(self, clip: AnimationClip):
        """Add an animation clip."""
        self.clips[clip.name] = clip
    
    def play(self, clip_name: str, blend: bool = True):
        """Play an animation clip.
        
        Args:
            clip_name: Name of clip to play
            blend: Whether to blend from current pose
        """
        if clip_name not in self.clips:
            return
        
        if blend and self.current_clip:
            # Store current pose for blending
            current_clip = self.clips[self.current_clip]
            self.previous_pose = current_clip.get_pose(self.current_time)
            self.blend_progress = 0.0
        else:
            self.blend_progress = 1.0
        
        self.current_clip = clip_name
        self.current_time = 0.0
        self.playing = True
    
    def update(self, dt: float):
        """Update animation.
        
        Args:
            dt: Delta time in seconds
        """
        if not self.playing or not self.current_clip:
            return
        
        clip = self.clips[self.current_clip]
        self.current_time += dt
        
        # Get current pose
        current_pose = clip.get_pose(self.current_time)
        
        # Blend with previous pose if transitioning
        if self.blend_progress < 1.0:
            self.blend_progress = min(1.0, self.blend_progress + dt / self.blend_time)
            
            if self.previous_pose:
                # Blend between previous and current
                blended_pose = {}
                for bone_name in current_pose:
                    if bone_name in self.previous_pose:
                        blended_pose[bone_name] = self.previous_pose[bone_name].lerp(
                            current_pose[bone_name], self.blend_progress
                        )
                    else:
                        blended_pose[bone_name] = current_pose[bone_name]
                current_pose = blended_pose
        
        # Apply pose to rig
        self.rig.apply_pose(current_pose)
        
        # Stop if non-looping animation finished
        if not clip.looping and self.current_time >= clip.duration:
            self.playing = False


class ProceduralAnimator:
    """Procedural animation utilities for runtime-generated motion."""
    
    @staticmethod
    def sine_wave(time: float, frequency: float, amplitude: float, offset: float = 0.0) -> float:
        """Generate sine wave value.
        
        Args:
            time: Current time
            frequency: Wave frequency
            amplitude: Wave amplitude
            offset: Phase offset
            
        Returns:
            Sine wave value
        """
        return math.sin(time * frequency + offset) * amplitude
    
    @staticmethod
    def breathe(time: float, intensity: float = 0.02) -> LVector3f:
        """Generate breathing motion (scale variation).
        
        Args:
            time: Current time
            intensity: Breathing intensity
            
        Returns:
            Scale vector for breathing
        """
        breathe_amount = math.sin(time * 2.0) * intensity
        return LVector3f(1.0, 1.0, 1.0 + breathe_amount)
    
    @staticmethod
    def head_bob(time: float, speed: float, intensity: float = 0.05) -> LVector3f:
        """Generate head bob motion for walking.
        
        Args:
            time: Current time
            speed: Movement speed
            intensity: Bob intensity
            
        Returns:
            Position offset for head bob
        """
        bob = abs(math.sin(time * speed * 2)) * intensity
        return LVector3f(0, 0, bob)
    
    @staticmethod
    def sway(time: float, frequency: float = 1.0, amplitude: float = 5.0) -> float:
        """Generate swaying rotation.
        
        Args:
            time: Current time
            frequency: Sway frequency
            amplitude: Sway amplitude in degrees
            
        Returns:
            Rotation angle in degrees
        """
        return math.sin(time * frequency) * amplitude
