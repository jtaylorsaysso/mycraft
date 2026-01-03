"""
VoxelAvatar: A skeleton-driven voxel character model.

Visual representation of the HumanoidSkeleton using simple voxel shapes (cubes).
Designed to be animated by the LayeredAnimator system.
"""

from typing import Dict, Optional, Tuple
from panda3d.core import NodePath, LVector3f, CardMaker

from engine.animation.skeleton import HumanoidSkeleton, Bone

class VoxelAvatar:
    """
    A rigged voxel avatar with visual nodes generated from a HumanoidSkeleton.
    """
    
    # Standardized bone thickness values for consistent visual representation
    BONE_THICKNESS_MAP = {
        "spine": 0.25,
        "chest": 0.35,
        "head": 0.25,
        "hips": 0.30,
        "thigh_left": 0.18,
        "thigh_right": 0.18,
        "shin_left": 0.15,
        "shin_right": 0.15,
        "upper_arm_left": 0.12,
        "upper_arm_right": 0.12,
        "forearm_left": 0.10,
        "forearm_right": 0.10,
        "shoulder_left": 0.15,
        "shoulder_right": 0.15,
        "hand_left": 0.08,
        "hand_right": 0.08,
        "foot_left": 0.12,
        "foot_right": 0.12,
    }
    
    def __init__(self, parent_node: NodePath, skeleton: Optional[HumanoidSkeleton] = None, body_color=(0.2, 0.8, 0.2, 1.0), validate: bool = True):
        """
        Initialize VoxelAvatar.
        
        Args:
            parent_node: Parent Panda3D NodePath.
            skeleton: Optional existing skeleton. If None, creates a new HumanoidSkeleton.
            body_color: Base color for the avatar.
            validate: If True, validate skeleton structure on initialization (default: True).
        """
        self.root = parent_node.attachNewNode("VoxelAvatar")
        self.body_color = body_color
        
        self.skeleton = skeleton if skeleton else HumanoidSkeleton()
        self.bone_nodes: Dict[str, NodePath] = {}
        
        # Runtime validation (opt-out via validate=False)
        if validate:
            self.validate_avatar()
        
        self._build_visuals()
        
    # Old _create_cube_visual removed. Logic moved to _create_bone_geometry.

    def _build_visuals(self):
        """Build visual nodes for all bones in skeleton."""
        # Recursively build bone hierarchy from root
        self._build_bone_hierarchy(self.skeleton.root)

    def _build_bone_hierarchy(self, bone: Bone, parent_node: Optional[NodePath] = None):
        """Recursively build bone hierarchy.
        
        Args:
            bone: Current bone processing
            parent_node: Parent NodePath (None for root)
        """
        # Determine parent for this bone's node
        # For root (hips), parent is main self.root
        effective_parent = parent_node if parent_node else self.root
        
        # Create NodePath for this bone
        # This NodePath represents the JOINT transform
        bone_node = effective_parent.attachNewNode(bone.name)
        self.bone_nodes[bone.name] = bone_node
        
        # Set default local transform (Skeleton T-Pose offset)
        # Transform from parent joint to this joint
        t = bone.local_transform
        bone_node.setPos(t.position)
        bone_node.setHpr(t.rotation.x, t.rotation.y, t.rotation.z)  # heading, pitch, roll
        # bone_node.setScale(t.scale) # Usually 1.0
        
        # Build Visual (if bone has length)
        # Visual is a child of the bone node, aligned along Y
        if bone.length > 0.01:
            # Get thickness from standardized map
            thickness = self.BONE_THICKNESS_MAP.get(bone.name, 0.1)
            self._create_bone_geometry(bone_node, bone.name, bone.length, thickness)
            
        # Recurse for children
        for child in bone.children:
            self._build_bone_hierarchy(child, bone_node)

    def _create_bone_geometry(self, parent_node: NodePath, name: str, length: float, thickness: float):
        """Create visual geometry for bone.
        
        Creates a 6-face cube using CardMaker. Each face is positioned and rotated
        to form a complete cube. Two-sided rendering is enabled to prevent backface culling issues.
        """
        cm = CardMaker(f"cm_{name}")
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)  # 1x1 card centered at origin
        
        # Container for geometry
        geom_holder = parent_node.attachNewNode(f"visual_{name}")
        
        # CardMaker creates cards in XZ plane, facing -Y by default.
        # For a cube centered at origin with faces at ±0.5 on each axis:
        # 
        # Face positions and rotations (H=heading around Z, P=pitch around X, R=roll around Y):
        # - Front (-Y face): at y=-0.5, needs to face -Y (default), no rotation
        # - Back (+Y face): at y=+0.5, needs to face +Y, rotate H=180
        # - Left (-X face): at x=-0.5, needs to face -X, rotate H=90
        # - Right (+X face): at x=+0.5, needs to face +X, rotate H=-90 (or 270)
        # - Top (+Z face): at z=+0.5, needs to face +Z, rotate P=-90
        # - Bottom (-Z face): at z=-0.5, needs to face -Z, rotate P=90
        
        face_definitions = [
            (LVector3f(0, -0.5, 0), LVector3f(0, 0, 0)),     # Front (-Y)
            (LVector3f(0, 0.5, 0), LVector3f(180, 0, 0)),    # Back (+Y)
            (LVector3f(-0.5, 0, 0), LVector3f(90, 0, 0)),    # Left (-X)
            (LVector3f(0.5, 0, 0), LVector3f(-90, 0, 0)),    # Right (+X)
            (LVector3f(0, 0, 0.5), LVector3f(0, -90, 0)),    # Top (+Z)
            (LVector3f(0, 0, -0.5), LVector3f(0, 90, 0)),    # Bottom (-Z)
        ]
        
        for pos, hpr in face_definitions:
            face = geom_holder.attachNewNode(cm.generate())
            face.setPos(pos)
            face.setHpr(hpr)
            # Enable two-sided rendering to prevent backface culling issues
            face.setTwoSided(True)
            
        geom_holder.setColorScale(self.body_color)
        
        # Scale to match bone dimensions
        # Visual aligns with Y axis (bone direction is +Y in local space)
        geom_holder.setScale(thickness, length, thickness)
        
        # Pivot is at start of bone (0,0,0)
        # Geometry center is at length/2 along Y so cube spans from 0 to length
        geom_holder.setPos(0, length / 2.0, 0)

    def validate_avatar(self) -> None:
        """Validate skeleton structure and avatar integrity.
        
        Raises:
            ValueError: If skeleton is invalid or avatar has structural issues
        """
        # Validate skeleton structure
        if isinstance(self.skeleton, HumanoidSkeleton):
            self.skeleton.validate_structure()
            self.skeleton.validate_constraints()
        
        # Validate all skeleton bones have thickness values
        missing_thickness = []
        for bone_name in self.skeleton.bones.keys():
            if bone_name not in self.BONE_THICKNESS_MAP:
                missing_thickness.append(bone_name)
        
        if missing_thickness:
            print(f"⚠️ Warning: Bones missing thickness values (will use default 0.1): {', '.join(missing_thickness)}")
    
    def cleanup(self):
        self.root.removeNode()
