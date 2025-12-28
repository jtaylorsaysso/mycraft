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
    
    def __init__(self, parent_node: NodePath, skeleton: Optional[HumanoidSkeleton] = None, body_color=(0.2, 0.8, 0.2, 1.0)):
        """
        Initialize VoxelAvatar.
        
        Args:
            parent_node: Parent Panda3D NodePath.
            skeleton: Optional existing skeleton. If None, creates a new HumanoidSkeleton.
            body_color: Base color for the avatar.
        """
        self.root = parent_node.attachNewNode("VoxelAvatar")
        self.body_color = body_color
        
        self.skeleton = skeleton if skeleton else HumanoidSkeleton()
        self.bone_nodes: Dict[str, NodePath] = {}
        
        self._build_visuals()
        
    # Old _create_cube_visual removed. Logic moved to _create_bone_geometry.

    def _build_visuals(self):
        """Build visual nodes for all bones in skeleton."""
        
        # Specific thickness tweaks for body parts
        thickness_map = {
            "spine": 0.25,
            "chest": 0.35,
            "head": 0.25,
            "hips": 0.30,
            
            "thigh_left": 0.18, "thigh_right": 0.18,
            "shin_left": 0.15, "shin_right": 0.15,
            
            "upper_arm_left": 0.12, "upper_arm_right": 0.12,
            "forearm_left": 0.10, "forearm_right": 0.10,
        }
        
        # 1. Create hierarchy of empty nodes (skeleton structure)
        # We traverse the bone list. Since skeleton.bones is a specific order,
        # we need to ensure parents are created before children.
        # But dictionary order isn't guaranteed (though in Py3.7+ it is insertion order).
        # Safe way: recursive traversal from root.
        
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
            # We want visual thickness
            thickness_map = {
                "spine": 0.25, "chest": 0.35, "head": 0.25, "hips": 0.30,
                "thigh_left": 0.18, "thigh_right": 0.18,
                "shin_left": 0.15, "shin_right": 0.15,
                "upper_arm_left": 0.12, "upper_arm_right": 0.12,
                "forearm_left": 0.10, "forearm_right": 0.10,
                "shoulder_left": 0.15, "shoulder_right": 0.15, 
            }
            thickness = thickness_map.get(bone.name, 0.1)
            
            self._create_bone_geometry(bone_node, bone.name, bone.length, thickness)
            
        # Recurse for children
        for child in bone.children:
            self._build_bone_hierarchy(child, bone_node)

    def _create_bone_geometry(self, parent_node: NodePath, name: str, length: float, thickness: float):
        """Create visual geometry for bone."""
        cm = CardMaker(f"cm_{name}")
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)
        
        # Container for geometry
        geom_holder = parent_node.attachNewNode(f"visual_{name}")
        
        # Create cube faces
        for face_info in [
            (LVector3f(0, -0.5, 0), LVector3f(0, 0, 0)),    # Front
            (LVector3f(0, 0.5, 0), LVector3f(180, 0, 0)),   # Back
            (LVector3f(-0.5, 0, 0), LVector3f(90, 0, 0)),   # Left
            (LVector3f(0.5, 0, 0), LVector3f(-90, 0, 0)),   # Right
            (LVector3f(0, 0, 0.5), LVector3f(0, -90, 0)),   # Top
            (LVector3f(0, 0, -0.5), LVector3f(0, 90, 0)),   # Bottom
        ]:
            face = geom_holder.attachNewNode(cm.generate())
            face.setPos(face_info[0])
            face.setHpr(face_info[1])
            
        geom_holder.setColorScale(self.body_color)
        
        # Scale to match bone dimensions
        # Visual aligns with Y axis (Forward)
        geom_holder.setScale(thickness, length, thickness)
        
        # Pivot is at start of bone (0,0,0)
        # Geometry center is at length/2 along Y
        geom_holder.setPos(0, length / 2.0, 0)

    def cleanup(self):
        self.root.removeNode()
