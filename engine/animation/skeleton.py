"""Articulated skeleton system for character animation.

Provides hierarchical bone structures with forward kinematics (FK) and constraints.
Designed for voxel characters with articulated limbs (elbows, knees, etc.).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from panda3d.core import NodePath, LVector3f, LQuaternionf
import math


@dataclass
class BoneConstraints:
    """Rotation constraints for a bone.
    
    Defines min/max angles for each rotation axis to prevent
    unnatural joint bending.
    """
    # Euler angles in degrees (heading, pitch, roll)
    min_h: float = -180.0
    max_h: float = 180.0
    min_p: float = -180.0
    max_p: float = 180.0
    min_r: float = -180.0
    max_r: float = 180.0
    
    def clamp(self, h: float, p: float, r: float) -> Tuple[float, float, float]:
        """Clamp angles to constraints.
        
        Args:
            h: Heading angle in degrees
            p: Pitch angle in degrees
            r: Roll angle in degrees
            
        Returns:
            Clamped (h, p, r) tuple
        """
        return (
            max(self.min_h, min(self.max_h, h)),
            max(self.min_p, min(self.max_p, p)),
            max(self.min_r, min(self.max_r, r))
        )


# Import Transform from core
from engine.animation.core import Transform


class Bone:
    """Single bone in a hierarchical skeleton.
    
    Represents a joint with position, rotation, and parent/child relationships.
    Used for both forward kinematics (FK) and inverse kinematics (IK).
    """
    
    def __init__(
        self,
        name: str,
        length: float,
        parent: Optional['Bone'] = None,
        constraints: Optional[BoneConstraints] = None
    ):
        """Initialize bone.
        
        Args:
            name: Unique bone identifier (e.g., 'upper_arm_left')
            length: Bone length in world units
            parent: Parent bone (None for root)
            constraints: Rotation constraints
        """
        self.name = name
        self.length = length
        self.parent = parent
        self.children: List['Bone'] = []
        self.constraints = constraints or BoneConstraints()
        
        # Transforms
        self.local_transform = Transform()  # Relative to parent
        self.world_transform = Transform()  # Absolute position
        
        # Auto-register with parent
        if parent:
            parent.children.append(self)
    
    def set_local_rotation(self, h: float, p: float, r: float, apply_constraints: bool = True):
        """Set local rotation with optional constraint clamping.
        
        Args:
            h: Heading (yaw) in degrees
            p: Pitch in degrees
            r: Roll in degrees
            apply_constraints: Whether to apply joint constraints
        """
        if apply_constraints:
            h, p, r = self.constraints.clamp(h, p, r)
        
        self.local_transform.rotation = LVector3f(h, p, r)
    
    def update_world_transform(self):
        """Update world transform from parent chain (FK).
        
        Call this after modifying local transforms to propagate
        changes down the hierarchy.
        """
        if self.parent:
            # Combine parent world transform with our local transform
            # This is simplified - in production you'd use proper matrix multiplication
            parent_pos = self.parent.world_transform.position
            parent_rot = self.parent.world_transform.rotation
            
            # Apply parent rotation to our local position offset
            # For now, simple addition (proper implementation would rotate the offset)
            self.world_transform.position = parent_pos + self.local_transform.position
            self.world_transform.rotation = parent_rot + self.local_transform.rotation
            self.world_transform.scale = self.local_transform.scale
        else:
            # Root bone - world = local (copy values, not reference)
            pos = self.local_transform.position
            rot = self.local_transform.rotation
            scl = self.local_transform.scale
            self.world_transform.position = LVector3f(pos.x, pos.y, pos.z)
            self.world_transform.rotation = LVector3f(rot.x, rot.y, rot.z)
            self.world_transform.scale = LVector3f(scl.x, scl.y, scl.z)
        
        # Recursively update children
        for child in self.children:
            child.update_world_transform()
    
    def get_end_position(self) -> LVector3f:
        """Get world position of bone end (tip).
        
        Returns:
            World position of bone end point
        """
        # Bone extends along local +Y axis
        # In proper implementation, this would be rotated by world rotation
        offset = LVector3f(0, self.length, 0)
        return self.world_transform.position + offset


class Skeleton:
    """Hierarchical bone structure for character animation.
    
    Manages bone hierarchy, forward kinematics updates, and bone queries.
    """
    
    def __init__(self, root_name: str = "root"):
        """Initialize skeleton with root bone.
        
        Args:
            root_name: Name for root bone
        """
        self.root = Bone(root_name, length=0.0)  # Root has no length
        self.bones: Dict[str, Bone] = {root_name: self.root}
    
    def add_bone(
        self,
        name: str,
        parent_name: str,
        length: float,
        constraints: Optional[BoneConstraints] = None
    ) -> Bone:
        """Add a new bone to the skeleton.
        
        Args:
            name: Unique bone identifier
            parent_name: Name of parent bone
            length: Bone length
            constraints: Optional rotation constraints
            
        Returns:
            Created bone
            
        Raises:
            ValueError: If parent doesn't exist or name already used
        """
        if name in self.bones:
            raise ValueError(f"Bone '{name}' already exists")
        
        if parent_name not in self.bones:
            raise ValueError(f"Parent bone '{parent_name}' not found")
        
        parent = self.bones[parent_name]
        bone = Bone(name, length, parent, constraints)
        self.bones[name] = bone
        return bone
    
    def get_bone(self, name: str) -> Optional[Bone]:
        """Get bone by name.
        
        Args:
            name: Bone name
            
        Returns:
            Bone if found, None otherwise
        """
        return self.bones.get(name)
    
    def get_chain(self, from_bone: str, to_bone: str) -> List[Bone]:
        """Get bone chain from one bone to another.
        
        Used for IK solving - returns path through hierarchy.
        
        Args:
            from_bone: Start bone name (typically closer to root)
            to_bone: End bone name (end effector)
            
        Returns:
            List of bones from start to end (inclusive)
            
        Raises:
            ValueError: If bones don't exist or aren't connected
        """
        start = self.bones.get(from_bone)
        end = self.bones.get(to_bone)
        
        if not start or not end:
            raise ValueError("Bone not found")
        
        # Walk from end to start, building chain backward
        chain = []
        current = end
        
        while current:
            chain.append(current)
            if current == start:
                break
            current = current.parent
        
        if chain[-1] != start:
            raise ValueError(f"'{to_bone}' is not descendant of '{from_bone}'")
        
        # Reverse to go from root to tip
        chain.reverse()
        return chain
    
    def update_world_transforms(self):
        """Update all world transforms via forward kinematics.
        
        Call this after modifying any local transforms to propagate
        changes through the entire skeleton.
        """
        self.root.update_world_transform()
    
    def apply_to_nodes(self, node_map: Dict[str, NodePath]):
        """Apply skeleton transforms to Panda3D nodes.
        
        Args:
            node_map: Dictionary mapping bone names to NodePaths
        """
        for name, bone in self.bones.items():
            if name in node_map:
                bone.world_transform.apply_to_node(node_map[name])


class HumanoidSkeleton(Skeleton):
    """Preset 17-bone humanoid skeleton.
    
    Pre-configured skeleton with ergonomic constraints for bipedal characters.
    
    Bone hierarchy:
        root (hips)
        ├── spine
        │   ├── chest
        │   │   ├── head
        │   │   ├── shoulder_left
        │   │   │   ├── upper_arm_left
        │   │   │   └── forearm_left
        │   │   │       └── hand_left
        │   │   └── shoulder_right
        │   │       ├── upper_arm_right
        │   │       └── forearm_right
        │   │           └── hand_right
        ├── thigh_left
        │   └── shin_left
        │       └── foot_left
        └── thigh_right
            └── shin_right
                └── foot_right
    """
    
    # Bone length constants (in voxel units)
    SPINE_LENGTH = 0.8
    CHEST_LENGTH = 0.6
    HEAD_LENGTH = 0.5
    SHOULDER_LENGTH = 0.3
    UPPER_ARM_LENGTH = 0.6
    FOREARM_LENGTH = 0.6
    HAND_LENGTH = 0.3
    THIGH_LENGTH = 0.8
    SHIN_LENGTH = 0.8
    FOOT_LENGTH = 0.4
    
    def __init__(self):
        """Initialize humanoid skeleton with all bones and constraints."""
        super().__init__(root_name="hips")
        
        # Spine chain
        self.add_bone("spine", "hips", self.SPINE_LENGTH)
        self.add_bone("chest", "spine", self.CHEST_LENGTH)
        self.add_bone("head", "chest", self.HEAD_LENGTH,
                     BoneConstraints(min_p=-45, max_p=45, min_h=-60, max_h=60))
        
        # Left arm chain
        self.add_bone("shoulder_left", "chest", self.SHOULDER_LENGTH)
        self.add_bone("upper_arm_left", "shoulder_left", self.UPPER_ARM_LENGTH,
                     BoneConstraints(min_p=-180, max_p=180, min_h=-90, max_h=180))
        self.add_bone("forearm_left", "upper_arm_left", self.FOREARM_LENGTH,
                     BoneConstraints(min_p=0, max_p=150))  # Elbow only bends one way
        self.add_bone("hand_left", "forearm_left", self.HAND_LENGTH)
        
        # Right arm chain
        self.add_bone("shoulder_right", "chest", self.SHOULDER_LENGTH)
        self.add_bone("upper_arm_right", "shoulder_right", self.UPPER_ARM_LENGTH,
                     BoneConstraints(min_p=-180, max_p=180, min_h=-180, max_h=90))
        self.add_bone("forearm_right", "upper_arm_right", self.FOREARM_LENGTH,
                     BoneConstraints(min_p=0, max_p=150))
        self.add_bone("hand_right", "forearm_right", self.HAND_LENGTH)
        
        # Left leg chain
        self.add_bone("thigh_left", "hips", self.THIGH_LENGTH,
                     BoneConstraints(min_p=-120, max_p=60))
        self.add_bone("shin_left", "thigh_left", self.SHIN_LENGTH,
                     BoneConstraints(min_p=-150, max_p=0))  # Knee only bends backward
        self.add_bone("foot_left", "shin_left", self.FOOT_LENGTH)
        
        # Right leg chain
        self.add_bone("thigh_right", "hips", self.THIGH_LENGTH,
                     BoneConstraints(min_p=-120, max_p=60))
        self.add_bone("shin_right", "thigh_right", self.SHIN_LENGTH,
                     BoneConstraints(min_p=-150, max_p=0))
        self.add_bone("foot_right", "shin_right", self.FOOT_LENGTH)
        
        # Set initial local positions (offsets from parent)
        self._set_default_pose()
    
    def _set_default_pose(self):
        """Set T-pose as default skeleton configuration."""
        # Position bones relative to their parents
        
        # Spine is centered above hips
        self.bones["spine"].local_transform.position = LVector3f(0, 0, 0)
        self.bones["chest"].local_transform.position = LVector3f(0, 0, self.SPINE_LENGTH)
        self.bones["head"].local_transform.position = LVector3f(0, 0, self.CHEST_LENGTH)
        
        # Arms extend to sides (T-pose)
        self.bones["shoulder_left"].local_transform.position = LVector3f(-0.3, 0, self.CHEST_LENGTH * 0.8)
        self.bones["upper_arm_left"].local_transform.position = LVector3f(-0.1, 0, 0)
        self.bones["forearm_left"].local_transform.position = LVector3f(-self.UPPER_ARM_LENGTH, 0, 0)
        self.bones["hand_left"].local_transform.position = LVector3f(-self.FOREARM_LENGTH, 0, 0)
        
        self.bones["shoulder_right"].local_transform.position = LVector3f(0.3, 0, self.CHEST_LENGTH * 0.8)
        self.bones["upper_arm_right"].local_transform.position = LVector3f(0.1, 0, 0)
        self.bones["forearm_right"].local_transform.position = LVector3f(self.UPPER_ARM_LENGTH, 0, 0)
        self.bones["hand_right"].local_transform.position = LVector3f(self.FOREARM_LENGTH, 0, 0)
        
        # Legs hang down
        self.bones["thigh_left"].local_transform.position = LVector3f(-0.2, 0, 0)
        self.bones["shin_left"].local_transform.position = LVector3f(0, 0, -self.THIGH_LENGTH)
        self.bones["foot_left"].local_transform.position = LVector3f(0, 0, -self.SHIN_LENGTH)
        
        self.bones["thigh_right"].local_transform.position = LVector3f(0.2, 0, 0)
        self.bones["shin_right"].local_transform.position = LVector3f(0, 0, -self.THIGH_LENGTH)
        self.bones["foot_right"].local_transform.position = LVector3f(0, 0, -self.SHIN_LENGTH)
        
        # Update world transforms
        self.update_world_transforms()
