"""Foot IK controller for terrain-aware foot placement.

Automatically adjusts foot positions based on terrain height,
creating natural-looking stances on slopes and uneven ground.
"""

from typing import Dict, Optional, Callable
from panda3d.core import LVector3f

from engine.animation.ik import IKTarget
from engine.animation.skeleton import Skeleton


class FootIKController:
    """Automatic foot placement on terrain using IK.
    
    Raycasts down from foot positions to find ground, then sets
    IK targets to plant feet naturally on the terrain.
    """
    
    def __init__(
        self,
        raycast_callback: Callable[[LVector3f, LVector3f], Optional[LVector3f]],
        hip_adjustment: float = 0.8,
        foot_offset: float = 0.1
    ):
        """Initialize foot IK controller.
        
        Args:
            raycast_callback: Function(origin, direction) -> hit_point
            hip_adjustment: How much to lower hips on slopes (0-1)
            foot_offset: Distance above ground to place foot
        """
        self.raycast_callback = raycast_callback
        self.hip_adjustment = hip_adjustment
        self.foot_offset = foot_offset
        self.enabled = True
        self._foot_bones = ["foot_left", "foot_right"]
    
    def update(
        self,
        skeleton: Skeleton,
        world_position: LVector3f,
        grounded: bool = True
    ) -> Dict[str, IKTarget]:
        """Update foot IK targets based on terrain.
        
        Args:
            skeleton: Character skeleton
            world_position: Character world position
            grounded: Whether character is on ground
            
        Returns:
            Dictionary of IK targets (bone_name -> IKTarget)
        """
        if not self.enabled or not grounded:
            return {}
        
        targets = {}
        ground_heights = []
        
        # Raycast from each foot to find ground
        for foot_bone_name in self._foot_bones:
            foot_bone = skeleton.get_bone(foot_bone_name)
            if not foot_bone:
                continue
            
            # Get foot position in world space
            foot_world_pos = world_position + foot_bone.world_transform.position
            
            # Raycast down to find ground
            raycast_origin = LVector3f(foot_world_pos.x, foot_world_pos.y, foot_world_pos.z + 2.0)
            raycast_direction = LVector3f(0, 0, -1)
            
            hit_point = self.raycast_callback(raycast_origin, raycast_direction)
            
            if hit_point:
                # Create IK target at ground position
                target_position = LVector3f(
                    foot_world_pos.x,
                    foot_world_pos.y,
                    hit_point.z + self.foot_offset
                )
                
                targets[foot_bone_name] = IKTarget(
                    position=target_position,
                    bone_name=foot_bone_name,
                    weight=1.0
                )
                
                ground_heights.append(hit_point.z)
        
        # Adjust hip height if on slope
        if len(ground_heights) >= 2 and self.hip_adjustment > 0:
            # Find lowest foot
            min_height = min(ground_heights)
            max_height = max(ground_heights)
            height_diff = max_height - min_height
            
            # Lower hips to keep natural pose on slopes
            if height_diff > 0.1:  # Only adjust if slope is significant
                hip_bone = skeleton.get_bone("hips")
                if hip_bone:
                    hip_adjustment = -height_diff * self.hip_adjustment
                    targets["hips"] = IKTarget(
                        position=LVector3f(
                            hip_bone.world_transform.position.x,
                            hip_bone.world_transform.position.y,
                            hip_bone.world_transform.position.z + hip_adjustment
                        ),
                        bone_name="hips",
                        weight=0.5  # Partial weight for smooth adjustment
                    )
        
        return targets
    
    def set_enabled(self, enabled: bool):
        """Enable or disable foot IK.
        
        Args:
            enabled: Whether foot IK is active
        """
        self.enabled = enabled
    
    def set_hip_adjustment(self, adjustment: float):
        """Set hip adjustment amount.
        
        Args:
            adjustment: Hip adjustment factor (0-1)
        """
        self.hip_adjustment = max(0.0, min(1.0, adjustment))
