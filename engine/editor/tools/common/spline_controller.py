"""
SplineController: Manages spine bones and distributes them along a spline.

Handles the logic of positioning and rotating spine bones to follow a curve.
"""

from typing import List, Optional
from panda3d.core import LVector3f, LQuaternionf
import math

from engine.animation.skeleton import Skeleton
from engine.editor.tools.common.spine_spline import SpineSpline
from engine.core.logger import get_logger

logger = get_logger(__name__)


class SplineController:
    """Controls spine bone distribution along a spline curve.
    
    Manages:
    - Spine bone list (hips, spine, chest)
    - Spline initialization from current skeleton
    - Bone redistribution along curve
    - Rotation alignment with tangent vectors
    """
    
    # Spine bone names in hierarchical order
    SPINE_BONES = ["hips", "spine", "chest"]
    
    def __init__(self, skeleton: Skeleton):
        """Initialize spine controller.
        
        Args:
            skeleton: Skeleton to control
        """
        self.skeleton = skeleton
        self.spline: Optional[SpineSpline] = None
        
    def initialize_from_skeleton(self):
        """Initialize spline from current skeleton bone positions.
        
        Creates a 4-point spline:
        - p0: hips - offset (for tangent)
        - p1: hips
        - p2: chest
        - p3: chest + offset (for tangent)
        """
        # Get spine bone positions
        hips_bone = self.skeleton.get_bone("hips")
        chest_bone = self.skeleton.get_bone("chest")
        
        if not hips_bone or not chest_bone:
            logger.warning("Cannot initialize spine: missing hips or chest")
            return
            
        # Get world positions (accounting for hierarchy)
        hips_pos = hips_bone.local_transform.position
        chest_pos = self._get_world_position("chest")
        
        # Compute offset for end control points
        spine_vec = chest_pos - hips_pos
        offset_dist = spine_vec.length() * 0.3
        spine_dir = spine_vec
        if spine_vec.length() > 0.0001:
            spine_dir = spine_vec / spine_vec.length()
        
        # Create 4-point spline
        # p0: before hips (for smooth tangent)
        p0 = hips_pos - spine_dir * offset_dist
        # p1: hips
        p1 = hips_pos
        # p2: chest
        p2 = chest_pos
        # p3: after chest (for smooth tangent)
        p3 = chest_pos + spine_dir * offset_dist
        
        self.spline = SpineSpline([p0, p1, p2, p3])
        logger.debug(f"Initialized spine spline from skeleton")
        
    def update_from_spline(self):
        """Update skeleton bone positions/rotations from current spline.
        
        Distributes bones evenly along the curve and rotates them
        to align with the curve's tangent.
        """
        if not self.spline:
            logger.warning("Cannot update: spline not initialized")
            return
            
        # Distribute bones along curve
        # t=0 → hips
        # t=0.5 → spine (midpoint)
        # t=1 → chest
        t_values = [0.0, 0.5, 1.0]
        
        for i, bone_name in enumerate(self.SPINE_BONES):
            t = t_values[i]
            bone = self.skeleton.get_bone(bone_name)
            
            if not bone:
                continue
                
            # Get position and tangent from spline
            position = self.spline.evaluate(t)
            tangent = self.spline.tangent(t)
            
            # Update bone position
            if bone_name == "hips":
                # Hips is root, use world position directly
                bone.local_transform.position = position
            else:
                # Other bones: convert to local space relative to parent
                parent = self.skeleton.get_bone(bone.parent_name)
                if parent:
                    parent_world_pos = self._get_world_position(bone.parent_name)
                    local_pos = position - parent_world_pos
                    bone.local_transform.position = local_pos
            
            # Update bone rotation to align with tangent
            rotation_hpr = self._tangent_to_hpr(tangent)
            bone.local_transform.rotation = rotation_hpr
            
        logger.debug("Updated bones from spline")
    
    def _get_world_position(self, bone_name: str) -> LVector3f:
        """Get world position of a bone (accounting for parent hierarchy).
        
        Args:
            bone_name: Name of the bone
            
        Returns:
            World position
        """
        bone = self.skeleton.get_bone(bone_name)
        if not bone:
            return LVector3f(0, 0, 0)
            
        # Walk up hierarchy
        pos = LVector3f(bone.local_transform.position)
        current = bone
        
        while current.parent_name:
            parent = self.skeleton.get_bone(current.parent_name)
            if not parent:
                break
            # Add parent's local position
            pos += parent.local_transform.position
            current = parent
            
        return pos
    
    def _tangent_to_hpr(self, tangent: LVector3f) -> LVector3f:
        """Convert a tangent vector to Heading-Pitch-Roll rotation.
        
        Args:
            tangent: Direction vector (normalized)
            
        Returns:
            HPR rotation in degrees
        """
        # Heading: rotation around Z axis (yaw)
        # atan2(y, x)
        heading = math.degrees(math.atan2(tangent.y, tangent.x))
        
        # Pitch: rotation around Y axis
        # atan2(z, horizontal_dist)
        horizontal_dist = math.sqrt(tangent.x**2 + tangent.y**2)
        pitch = math.degrees(math.atan2(tangent.z, horizontal_dist))
        
        # Roll: no automatic roll for spine
        roll = 0.0
        
        return LVector3f(heading, pitch, roll)
    
    def move_control_point(self, index: int, new_position: LVector3f):
        """Move a spline control point.
        
        Args:
            index: Control point index (0-3)
            new_position: New world position
        """
        if not self.spline:
            logger.warning("Cannot move control point: spline not initialized")
            return
            
        self.spline.set_control_point(index, new_position)
        logger.debug(f"Moved control point {index}")
        
    def get_control_points(self) -> List[LVector3f]:
        """Get current spline control points.
        
        Returns:
            List of control point positions
        """
        if not self.spline:
            return []
        return self.spline.get_control_points()
