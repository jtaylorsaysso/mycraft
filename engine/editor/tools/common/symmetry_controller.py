"""
SymmetryController: Automatic bilateral mirroring for humanoid skeletons.

Mirrors transform edits from left bones to right bones and vice versa.
"""

from typing import Optional, Dict
from panda3d.core import LVector3f
from engine.animation.skeleton import Skeleton, Bone
from engine.core.logger import get_logger

logger = get_logger(__name__)


# Bone pairing for humanoid skeletons
SYMMETRY_PAIRS = {
    "shoulder_left": "shoulder_right",
    "shoulder_right": "shoulder_left",
    "upper_arm_left": "upper_arm_right",
    "upper_arm_right": "upper_arm_left",
    "forearm_left": "forearm_right",
    "forearm_right": "forearm_left",
    "hand_left": "hand_right",
    "hand_right": "hand_left",
    "thigh_left": "thigh_right",
    "thigh_right": "thigh_left",
    "shin_left": "shin_right",
    "shin_right": "shin_left",
    "foot_left": "foot_right",
    "foot_right": "foot_left",
}


class SymmetryController:
    """Handles automatic bilateral symmetry for skeleton editing.
    
    Features:
    - Mirrors position (X-axis flip)
    - Mirrors rotation (heading inverted)
    - Mirrors length (same value)
    - Toggle on/off
    """
    
    def __init__(self, skeleton: Skeleton):
        """Initialize symmetry controller.
        
        Args:
            skeleton: Skeleton to apply symmetry to
        """
        self.skeleton = skeleton
        self.enabled = True
        self.pairs = SYMMETRY_PAIRS.copy()
        
    def set_enabled(self, enabled: bool):
        """Enable or disable symmetry.
        
        Args:
            enabled: Whether symmetry is active
        """
        self.enabled = enabled
        logger.debug(f"Symmetry {'enabled' if enabled else 'disabled'}")
        
    def get_mirror_bone(self, bone_name: str) -> Optional[str]:
        """Get the paired bone name for symmetry.
        
        Args:
            bone_name: Name of bone to find pair for
            
        Returns:
            Paired bone name, or None if unpaired (e.g., spine, head)
        """
        return self.pairs.get(bone_name)
        
    def mirror_position(self, bone_name: str, position: LVector3f):
        """Mirror a position change to the paired bone.
        
        Args:
            bone_name: Source bone name
            position: New position for source bone
        """
        if not self.enabled:
            return
            
        mirror_name = self.get_mirror_bone(bone_name)
        if not mirror_name:
            return
            
        mirror_bone = self.skeleton.get_bone(mirror_name)
        if not mirror_bone:
            return
            
        # Mirror across X axis (flip X component)
        mirrored_pos = LVector3f(-position.x, position.y, position.z)
        mirror_bone.local_transform.position = mirrored_pos
        
        logger.debug(f"Mirrored position {bone_name} -> {mirror_name}")
        
    def mirror_rotation(self, bone_name: str, rotation: LVector3f):
        """Mirror a rotation change to the paired bone.
        
        Args:
            bone_name: Source bone name
            rotation: New rotation (H, P, R) for source bone
        """
        if not self.enabled:
            return
            
        mirror_name = self.get_mirror_bone(bone_name)
        if not mirror_name:
            return
            
        mirror_bone = self.skeleton.get_bone(mirror_name)
        if not mirror_bone:
            return
            
        # Mirror rotation: invert heading (turn), keep pitch and roll
        mirrored_rot = LVector3f(-rotation.x, rotation.y, rotation.z)
        mirror_bone.local_transform.rotation = mirrored_rot
        
        logger.debug(f"Mirrored rotation {bone_name} -> {mirror_name}")
        
    def mirror_length(self, bone_name: str, length: float):
        """Mirror a length change to the paired bone.
        
        Args:
            bone_name: Source bone name
            length: New length for source bone
        """
        if not self.enabled:
            return
            
        mirror_name = self.get_mirror_bone(bone_name)
        if not mirror_name:
            return
            
        mirror_bone = self.skeleton.get_bone(mirror_name)
        if not mirror_bone:
            return
            
        # Length is the same for both sides
        mirror_bone.length = length
        
        logger.debug(f"Mirrored length {bone_name} -> {mirror_name}")
        
    def mirror_transform(self, bone_name: str):
        """Mirror all transform components of a bone.
        
        Convenience method that mirrors position, rotation, and length.
        
        Args:
            bone_name: Source bone name
        """
        if not self.enabled:
            return
            
        bone = self.skeleton.get_bone(bone_name)
        if not bone:
            return
            
        self.mirror_position(bone_name, bone.local_transform.position)
        self.mirror_rotation(bone_name, bone.local_transform.rotation)
        self.mirror_length(bone_name, bone.length)
        
    def apply_symmetry_to_all(self):
        """Apply symmetry from left bones to right bones for entire skeleton.
        
        Useful for initializing a symmetric pose.
        """
        if not self.enabled:
            return
            
        # Process all left bones
        for bone_name in self.skeleton.bones.keys():
            if "_left" in bone_name:
                self.mirror_transform(bone_name)
                
        logger.info("Applied symmetry to all paired bones")
