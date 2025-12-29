"""Animation layer system for blending multiple animation sources.

Enables compositing procedural locomotion, keyframe combat animations,
and IK corrections into a unified pose.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Set
from panda3d.core import LVector3f

from engine.animation.core import Transform
from engine.animation.skeleton import Skeleton


class BoneMask:
    """Defines which bones an animation layer affects.
    
    Bone masks allow layers to target specific body parts (e.g., upper body
    for combat animations while legs continue walking).
    """
    
    def __init__(self, bone_names: Optional[Set[str]] = None):
        """Initialize bone mask.
        
        Args:
            bone_names: Set of bone names to include. None = all bones.
        """
        self.bone_names = bone_names
    
    def affects_bone(self, bone_name: str) -> bool:
        """Check if this mask affects a given bone.
        
        Args:
            bone_name: Name of bone to check
            
        Returns:
            True if bone is affected by this mask
        """
        if self.bone_names is None:
            return True  # Full body mask
        return bone_name in self.bone_names
    
    @classmethod
    def full_body(cls) -> 'BoneMask':
        """Create a mask affecting all bones."""
        return cls(None)
    
    @classmethod
    def upper_body(cls) -> 'BoneMask':
        """Create a mask affecting chest and above."""
        return cls({
            'chest', 'head',
            'shoulder_left', 'upper_arm_left', 'forearm_left', 'hand_left',
            'shoulder_right', 'upper_arm_right', 'forearm_right', 'hand_right'
        })
    
    @classmethod
    def lower_body(cls) -> 'BoneMask':
        """Create a mask affecting hips and below."""
        return cls({
            'hips', 'spine',
            'thigh_left', 'shin_left', 'foot_left',
            'thigh_right', 'shin_right', 'foot_right'
        })
    
    @classmethod
    def arms(cls) -> 'BoneMask':
        """Create a mask affecting both arms."""
        return cls({
            'shoulder_left', 'upper_arm_left', 'forearm_left', 'hand_left',
            'shoulder_right', 'upper_arm_right', 'forearm_right', 'hand_right'
        })
    
    @classmethod
    def legs(cls) -> 'BoneMask':
        """Create a mask affecting both legs."""
        return cls({
            'thigh_left', 'shin_left', 'foot_left',
            'thigh_right', 'shin_right', 'foot_right'
        })


class AnimationSource(Protocol):
    """Protocol for animation sources that can drive a layer.
    
    Animation sources can be:
    - Procedural animations (walk cycles, idle sway)
    - Keyframe animations (combat moves, emotes)
    - IK solvers (foot placement, hand reach)
    """
    
    def update(self, dt: float, skeleton: Skeleton) -> Dict[str, Transform]:
        """Update and return bone transforms for this frame.
        
        Args:
            dt: Delta time since last frame
            skeleton: Skeleton to animate
            
        Returns:
            Dictionary mapping bone names to transforms
        """
        ...


@dataclass
class AnimationLayer:
    """Single animation layer with source, weight, and bone mask.
    
    Layers are composited by the LayeredAnimator to produce the final pose.
    Higher priority layers override lower priority layers for masked bones.
    """
    
    name: str
    source: AnimationSource
    weight: float = 1.0  # 0-1 blend weight
    mask: BoneMask = field(default_factory=BoneMask.full_body)
    priority: int = 0  # Higher priority = applied later (overrides)
    enabled: bool = True
    
    def get_transforms(self, dt: float, skeleton: Skeleton) -> Dict[str, Transform]:
        """Get transforms from this layer's source.
        
        Args:
            dt: Delta time
            skeleton: Skeleton to animate
            
        Returns:
            Bone transforms from source
        """
        if not self.enabled or self.weight <= 0.0:
            return {}
        
        return self.source.update(dt, skeleton)


class LayeredAnimator:
    """Composites multiple animation layers into a final pose.
    
    Layers are blended based on priority, weight, and bone masks:
    1. Layers sorted by priority (low to high)
    2. For each bone, blend transforms from all affecting layers
    3. Higher priority layers override lower priority for same bones
    
    Example usage:
        animator = LayeredAnimator(skeleton)
        animator.add_layer("locomotion", walk_source, priority=0)
        animator.add_layer("combat", attack_source, priority=10, mask=BoneMask.upper_body())
        animator.add_layer("ik", ik_source, priority=20)
        
        # Each frame:
        final_pose = animator.update(dt)
        animator.apply_to_skeleton()
    """
    
    def __init__(self, skeleton: Skeleton):
        """Initialize layered animator.
        
        Args:
            skeleton: Skeleton to animate
        """
        self.skeleton = skeleton
        self.layers: List[AnimationLayer] = []
        self._last_pose: Dict[str, Transform] = {}
    
    def add_layer(
        self,
        name: str,
        source: AnimationSource,
        priority: int = 0,
        weight: float = 1.0,
        mask: Optional[BoneMask] = None
    ) -> AnimationLayer:
        """Add a new animation layer.
        
        Args:
            name: Layer identifier
            source: Animation source for this layer
            priority: Layer priority (higher = applied later)
            weight: Blend weight (0-1)
            mask: Bone mask (None = full body)
            
        Returns:
            Created layer
        """
        if mask is None:
            mask = BoneMask.full_body()
        
        layer = AnimationLayer(
            name=name,
            source=source,
            weight=weight,
            mask=mask,
            priority=priority
        )
        
        self.layers.append(layer)
        self._sort_layers()
        return layer
    
    def remove_layer(self, name: str) -> bool:
        """Remove a layer by name.
        
        Args:
            name: Layer name
            
        Returns:
            True if layer was removed
        """
        for i, layer in enumerate(self.layers):
            if layer.name == name:
                self.layers.pop(i)
                return True
        return False
    
    def get_layer(self, name: str) -> Optional[AnimationLayer]:
        """Get layer by name.
        
        Args:
            name: Layer name
            
        Returns:
            Layer if found, None otherwise
        """
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None
    
    def set_layer_weight(self, name: str, weight: float):
        """Set layer blend weight.
        
        Args:
            name: Layer name
            weight: New weight (0-1)
        """
        layer = self.get_layer(name)
        if layer:
            layer.weight = max(0.0, min(1.0, weight))
    
    def set_layer_enabled(self, name: str, enabled: bool):
        """Enable or disable a layer.
        
        Args:
            name: Layer name
            enabled: Whether layer is enabled
        """
        layer = self.get_layer(name)
        if layer:
            layer.enabled = enabled
    
    def _sort_layers(self):
        """Sort layers by priority (low to high)."""
        self.layers.sort(key=lambda l: l.priority)
    
    def update(self, dt: float) -> Dict[str, Transform]:
        """Update all layers and blend into final pose.
        
        Args:
            dt: Delta time since last frame
            
        Returns:
            Final blended pose (bone name -> transform)
        """
        # Collect transforms from all layers
        layer_poses: List[tuple[AnimationLayer, Dict[str, Transform]]] = []
        
        for layer in self.layers:
            if layer.enabled and layer.weight > 0.0:
                transforms = layer.get_transforms(dt, self.skeleton)
                if transforms:
                    layer_poses.append((layer, transforms))
        
        # Blend layers into final pose
        final_pose: Dict[str, Transform] = {}
        
        for bone_name in self.skeleton.bones.keys():
            # Collect all transforms affecting this bone
            bone_transforms: List[tuple[float, Transform]] = []  # (weight, transform)
            
            for layer, transforms in layer_poses:
                if layer.mask.affects_bone(bone_name) and bone_name in transforms:
                    bone_transforms.append((layer.weight, transforms[bone_name]))
            
            # Blend transforms for this bone
            if bone_transforms:
                final_pose[bone_name] = self._blend_transforms(bone_transforms)
        
        self._last_pose = final_pose
        return final_pose
    
    def _blend_transforms(self, weighted_transforms: List[tuple[float, Transform]]) -> Transform:
        """Blend multiple transforms with weights.
        
        Args:
            weighted_transforms: List of (weight, transform) tuples
            
        Returns:
            Blended transform
        """
        if len(weighted_transforms) == 1:
            return weighted_transforms[0][1]
        
        # Normalize weights
        total_weight = sum(w for w, _ in weighted_transforms)
        if total_weight == 0:
            return Transform()
        
        # Weighted average of positions and rotations
        # Note: This is simplified - proper implementation should use quaternion slerp
        blended_pos = LVector3f(0, 0, 0)
        blended_rot = LVector3f(0, 0, 0)
        blended_scale = LVector3f(0, 0, 0)
        
        for weight, transform in weighted_transforms:
            normalized_weight = weight / total_weight
            blended_pos += transform.position * normalized_weight
            blended_rot += transform.rotation * normalized_weight
            blended_scale += transform.scale * normalized_weight
        
        return Transform(
            position=blended_pos,
            rotation=blended_rot,
            scale=blended_scale
        )
    
    def apply_to_skeleton(self):
        """Apply last computed pose to skeleton bones."""
        for bone_name, transform in self._last_pose.items():
            bone = self.skeleton.get_bone(bone_name)
            if bone:
                bone.local_transform = transform
        
        # Update world transforms via FK
        self.skeleton.update_world_transforms()
    
    def get_last_pose(self) -> Dict[str, Transform]:
        """Get the last computed pose.
        
        Returns:
            Last pose dictionary
        """
        return self._last_pose.copy()
