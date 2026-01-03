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
        # Transforms
        self.local_transform = Transform()  # Relative to parent
        self.world_transform = Transform()  # Absolute position
        self.rest_transform = Transform()   # T-Pose configuration
        
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
    
    # Canonical bone names for validation
    EXPECTED_BONE_NAMES = [
        "hips", "spine", "chest", "head",
        "shoulder_left", "upper_arm_left", "forearm_left", "hand_left",
        "shoulder_right", "upper_arm_right", "forearm_right", "hand_right",
        "thigh_left", "shin_left", "foot_left",
        "thigh_right", "shin_right", "foot_right"
    ]
    
    # Bone length constants (in voxel units)
    # Bone length constants (in voxel units)
    # Scaled for ~1.8m total height
    HIPS_LENGTH = 0.20  # Pelvic block
    SPINE_LENGTH = 0.3
    CHEST_LENGTH = 0.3
    HEAD_LENGTH = 0.25
    SHOULDER_LENGTH = 0.15
    UPPER_ARM_LENGTH = 0.35
    FOREARM_LENGTH = 0.35
    HAND_LENGTH = 0.15
    THIGH_LENGTH = 0.45
    SHIN_LENGTH = 0.45
    FOOT_LENGTH = 0.2
    
    def __init__(self):
        """Initialize humanoid skeleton with all bones and constraints."""
        super().__init__(root_name="hips")
        
        # Fix hips bone length (base Skeleton creates root with length=0)
        self.root.length = self.HIPS_LENGTH
        
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
        """Set T-pose as default skeleton configuration.
        
        With hierarchical structure:
        - Child node position is relative to Parent node position/rotation.
        - Visuals extend along +Y (forward/along bone).
        
        We need to set the LOCAL Position/Rotation of each bone relative to its parent 
        to achieve the T-Pose.
        """
        # 1. Root (Hips) Position - Absolute
        # Set height to match Leg Length (Thigh + Shin) + slight offset
        # Leg = 0.45 + 0.45 = 0.9. Hips at 0.95 puts feet just on ground.
        self.bones["hips"].local_transform.position = LVector3f(0, 0, 0.95)
        # Rotate Hips to point UP (+Z). This allows the pelvic block to align vertically.
        # Pivot is at bottom of pelvis, +Y extends Up.
        self.bones["hips"].local_transform.rotation = LVector3f(0, 90, 0) 
        
        # 2. Spine Chain (Upwards, +Z)
        # Spine is child of Hips. Hips are pointing Up.
        # Spine continues Up. Aligned with parent.
        self.bones["spine"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["spine"].local_transform.position = LVector3f(0, self.HIPS_LENGTH * 0.5, 0) # Start from middle of hips?
        # Actually Hips length is 0.2. Geometry center at 0.1.
        # Spine should start at top of Hips bone (0.2 up).
        self.bones["spine"].local_transform.position = LVector3f(0, self.HIPS_LENGTH, 0)
        
        # Chest (Child of Spine)
        # Spine is pointing Up. Chest continues Up.
        self.bones["chest"].local_transform.rotation = LVector3f(0, 0, 0) 
        self.bones["chest"].local_transform.position = LVector3f(0, self.SPINE_LENGTH, 0)
        
        # Head (Child of Chest)
        self.bones["head"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["head"].local_transform.position = LVector3f(0, self.CHEST_LENGTH, 0)
        
        # 3. Arms (Sideways, +/- X)
        # Shoulder Left (Child of Chest). Chest is pointing Up (World +Z).
        # We want Shoulder Left to point Left (World -X).
        # In Chest's local space (Aligned with World Z):
        # Local X=World X, Local Y=World Z, Local Z=World -Y (Right-handed)
        # Wait, if Chest Rot=(0,0,0) relative to Spine... relative to Hips(0,90,0)...
        # Hips(0,90,0): X->X, Y->Z, Z->-Y
        # So Chest Local Coordinates: X=World X, Y=World Z, Z=World -Y.
        
        # We want Shoulder Points Left (-X).
        # Rotation: Head 90 around local Z? No.
        # We want +Y (Bone Dir) to point -X.
        # Current local axes: X(Right), Y(Up), Z(Back)
        # Map Y->-X. Rotate 90 deg around Z.
        # Heading 90 in Panda (around Z).
        self.bones["shoulder_left"].local_transform.rotation = LVector3f(90, 0, 0)
        # Position: Offset from Chest Origin (Base of Chest).
        # Chest Origin is at top of Spine.
        # Ideally shoulder is near top of Chest.
        # Offset: Left(-X), Up(+Y).
        # Local Space (Y is Up).
        # So (-0.2, 0.9*Length, 0) is correct in this space.
        self.bones["shoulder_left"].local_transform.position = LVector3f(-0.20, self.CHEST_LENGTH * 0.9, 0)
        
        # Arms are children of Shoulder. Shoulder points -X.
        # Arms just extend along +Y (which is World -X).
        self.bones["upper_arm_left"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["upper_arm_left"].local_transform.position = LVector3f(0, self.SHOULDER_LENGTH, 0)
        
        self.bones["forearm_left"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["forearm_left"].local_transform.position = LVector3f(0, self.UPPER_ARM_LENGTH, 0)
        
        self.bones["hand_left"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["hand_left"].local_transform.position = LVector3f(0, self.FOREARM_LENGTH, 0)
        
        # Shoulder Right (Child of Chest). Points Right (World +X).
        # Map Y to +X. Heading -90.
        self.bones["shoulder_right"].local_transform.rotation = LVector3f(-90, 0, 0)
        self.bones["shoulder_right"].local_transform.position = LVector3f(0.20, self.CHEST_LENGTH * 0.9, 0)
        
        self.bones["upper_arm_right"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["upper_arm_right"].local_transform.position = LVector3f(0, self.SHOULDER_LENGTH, 0)
        
        self.bones["forearm_right"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["forearm_right"].local_transform.position = LVector3f(0, self.UPPER_ARM_LENGTH, 0)
        
        self.bones["hand_right"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["hand_right"].local_transform.position = LVector3f(0, self.FOREARM_LENGTH, 0)
        
        # 4. Legs (Downwards, -Z)
        # Thigh Left (Child of Hips). Hips are Pointing Up (World Z).
        # We want Thigh to point Down (World -Z).
        # Hips Space: Y is Up.
        # We want Thigh Y to be Down.
        # Rotation 180 degrees (Pitch).
        self.bones["thigh_left"].local_transform.rotation = LVector3f(0, 180, 0)
        
        # Position: Left(-X), Back(-Y in World).
        # Hips Space (X=WorldX, Y=WorldZ, Z=-WorldY).
        # Target World Offset: (-0.1, -0.05, 0).
        # Local X = -0.1.
        # Local Y (Up) = 0.
        # Local Z (Back) = 0.05 (since Z is -WorldY).
        self.bones["thigh_left"].local_transform.position = LVector3f(-0.10, 0, 0.05)
        
        # Legs extend along +Y (which is now Down/World -Z).
        self.bones["shin_left"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["shin_left"].local_transform.position = LVector3f(0, self.THIGH_LENGTH, 0)
        
        self.bones["foot_left"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["foot_left"].local_transform.position = LVector3f(0, self.SHIN_LENGTH, 0)
        
        self.bones["thigh_right"].local_transform.rotation = LVector3f(0, 180, 0)
        self.bones["thigh_right"].local_transform.position = LVector3f(0.10, 0, 0.05)
        
        self.bones["shin_right"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["shin_right"].local_transform.position = LVector3f(0, self.THIGH_LENGTH, 0)
        
        self.bones["foot_right"].local_transform.rotation = LVector3f(0, 0, 0)
        self.bones["foot_right"].local_transform.position = LVector3f(0, self.SHIN_LENGTH, 0)
        
        # Save this configuration as the rest pose
        for bone in self.bones.values():
            bone.rest_transform.position = LVector3f(bone.local_transform.position)
            bone.rest_transform.rotation = LVector3f(bone.local_transform.rotation)
            bone.rest_transform.scale = LVector3f(bone.local_transform.scale)

        # Update world transforms (still useful for logic that might read them, 
        # but not used for rendering anymore by us directly, though Panda does it under hood for nodes)
        self.update_world_transforms()
    
    @classmethod
    def get_expected_bones(cls) -> List[str]:
        """Get the canonical list of expected bone names.
        
        Returns:
            List of bone names that should be present in a valid HumanoidSkeleton
        """
        return cls.EXPECTED_BONE_NAMES.copy()
    
    def validate_structure(self) -> None:
        """Validate that skeleton has all expected bones with correct hierarchy.
        
        Raises:
            ValueError: If skeleton is missing bones or has incorrect structure
        """
        # Check all expected bones exist
        missing_bones = []
        for bone_name in self.EXPECTED_BONE_NAMES:
            if bone_name not in self.bones:
                missing_bones.append(bone_name)
        
        if missing_bones:
            raise ValueError(
                f"HumanoidSkeleton is missing required bones: {', '.join(missing_bones)}"
            )
        
        # Check for unexpected extra bones
        extra_bones = []
        for bone_name in self.bones.keys():
            if bone_name not in self.EXPECTED_BONE_NAMES:
                extra_bones.append(bone_name)
        
        if extra_bones:
            raise ValueError(
                f"HumanoidSkeleton has unexpected bones: {', '.join(extra_bones)}"
            )
        
        # Validate hierarchy relationships (spot checks for key chains)
        # Check spine chain
        spine_chain = self.get_chain("hips", "head")
        if len(spine_chain) != 4:  # hips -> spine -> chest -> head
            raise ValueError(
                f"Invalid spine chain: expected 4 bones, got {len(spine_chain)}"
            )
        
        # Check arm chains
        left_arm_chain = self.get_chain("shoulder_left", "hand_left")
        if len(left_arm_chain) != 4:  # shoulder -> upper_arm -> forearm -> hand
            raise ValueError(
                f"Invalid left arm chain: expected 4 bones, got {len(left_arm_chain)}"
            )
        
        right_arm_chain = self.get_chain("shoulder_right", "hand_right")
        if len(right_arm_chain) != 4:
            raise ValueError(
                f"Invalid right arm chain: expected 4 bones, got {len(right_arm_chain)}"
            )
        
        # Check leg chains
        left_leg_chain = self.get_chain("thigh_left", "foot_left")
        if len(left_leg_chain) != 3:  # thigh -> shin -> foot
            raise ValueError(
                f"Invalid left leg chain: expected 3 bones, got {len(left_leg_chain)}"
            )
        
        right_leg_chain = self.get_chain("thigh_right", "foot_right")
        if len(right_leg_chain) != 3:
            raise ValueError(
                f"Invalid right leg chain: expected 3 bones, got {len(right_leg_chain)}"
            )
    
    def validate_constraints(self) -> None:
        """Validate that key bones have appropriate rotation constraints.
        
        Raises:
            ValueError: If constraints are missing or incorrectly configured
        """
        # Check elbow constraints (should only bend one way)
        for elbow_name in ["forearm_left", "forearm_right"]:
            elbow = self.get_bone(elbow_name)
            if not elbow or not elbow.constraints:
                raise ValueError(f"Bone '{elbow_name}' missing constraints")
            
            # Elbows should have limited pitch range (0 to 150)
            if elbow.constraints.min_p != 0 or elbow.constraints.max_p != 150:
                raise ValueError(
                    f"Bone '{elbow_name}' has incorrect constraints: "
                    f"expected min_p=0, max_p=150, got min_p={elbow.constraints.min_p}, "
                    f"max_p={elbow.constraints.max_p}"
                )
        
        # Check knee constraints (should only bend backward)
        for knee_name in ["shin_left", "shin_right"]:
            knee = self.get_bone(knee_name)
            if not knee or not knee.constraints:
                raise ValueError(f"Bone '{knee_name}' missing constraints")
            
            # Knees should have limited pitch range (-150 to 0)
            if knee.constraints.min_p != -150 or knee.constraints.max_p != 0:
                raise ValueError(
                    f"Bone '{knee_name}' has incorrect constraints: "
                    f"expected min_p=-150, max_p=0, got min_p={knee.constraints.min_p}, "
                    f"max_p={knee.constraints.max_p}"
                )
