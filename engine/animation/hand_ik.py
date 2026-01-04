"""Hand IK controller for climbing and surface grabbing.

Automatically places hands on nearby surfaces using raycasts and IK,
enabling magnetic climbing mechanics on any surface.
"""

from typing import Dict, Optional, Callable
from panda3d.core import LVector3f
import math

from engine.animation.ik import IKTarget
from engine.animation.skeleton import Skeleton


class HandIKController:
    """Automatic hand placement on surfaces using IK.
    
    Raycasts from shoulders/head to find climbable surfaces, then sets
    IK targets to place hands naturally on walls for climbing.
    """
    
    def __init__(
        self,
        raycast_callback: Callable[[LVector3f, LVector3f], Optional[LVector3f]],
        reach_distance: float = 0.8,
        hand_offset: float = 0.05,
        update_interval: int = 2
    ):
        """Initialize hand IK controller.
        
        Args:
            raycast_callback: Function(origin, direction) -> hit_point
            reach_distance: Maximum distance hands can reach for surfaces
            hand_offset: Distance from surface to place hand (for thickness)
            update_interval: Frames between IK updates (2 = 30Hz at 60FPS)
        """
        self.raycast_callback = raycast_callback
        self.reach_distance = reach_distance
        self.hand_offset = hand_offset
        self.enabled = False  # Only active during climbing
        self._hand_bones = ["hand_left", "hand_right"]
        
        # Performance optimization: Update frequency control
        self.update_interval = update_interval
        self._frame_counter = 0
        self._last_targets = {}  # Cache last computed targets
    
    def update(
        self,
        skeleton: Skeleton,
        world_position: LVector3f,
        forward_direction: LVector3f,
        climbing: bool = False,
        dt: float = 0.0
    ) -> Dict[str, IKTarget]:
        """Update hand IK targets based on nearby surfaces.
        
        Args:
            skeleton: Character skeleton
            world_position: Character world position
            forward_direction: Direction character is facing
            climbing: Whether character is in climbing state
            dt: Delta time (for frame control)
            
        Returns:
            Dictionary of IK targets (bone_name -> IKTarget)
        """
        if not self.enabled or not climbing:
            return {}
        
        # Update frequency reduction
        self._frame_counter += 1
        if self._frame_counter % self.update_interval != 1:  # Compute on frames 1, 3, 5...
            return self._last_targets
        
        # Perform actual IK computation
        targets = self._compute_ik_targets(skeleton, world_position, forward_direction)
        self._last_targets = targets
        return targets
    
    def _compute_ik_targets(
        self,
        skeleton: Skeleton,
        world_position: LVector3f,
        forward_direction: LVector3f
    ) -> Dict[str, IKTarget]:
        """Compute IK targets for hands on surfaces."""
        targets = {}
        
        # Get chest position as raycast origin (approximate shoulder height)
        chest_bone = skeleton.get_bone("chest")
        if not chest_bone:
            return targets
        
        chest_world_pos = world_position + chest_bone.world_transform.position
        
        # Raycast for each hand
        for hand_bone_name in self._hand_bones:
            hand_bone = skeleton.get_bone(hand_bone_name)
            if not hand_bone:
                continue
            
            # Determine lateral offset for left/right hand
            is_left = "left" in hand_bone_name
            lateral_offset = -0.25 if is_left else 0.25  # Shoulder width
            
            # Calculate raycast origin (from shoulder area)
            # Offset laterally from chest center
            right_vector = LVector3f(
                -forward_direction.y,
                forward_direction.x,
                0
            )
            right_vector.normalize()
            
            raycast_origin = chest_world_pos + (right_vector * lateral_offset)
            
            # Raycast forward to find wall
            raycast_direction = forward_direction
            hit_point = self.raycast_callback(raycast_origin, raycast_direction)
            
            if hit_point:
                # Check if surface is within reach
                distance = (hit_point - raycast_origin).length()
                if distance <= self.reach_distance:
                    # Place hand on surface with offset for hand thickness
                    # Pull back slightly from surface
                    target_position = hit_point - (forward_direction * self.hand_offset)
                    
                    targets[hand_bone_name] = IKTarget(
                        position=target_position,
                        bone_name=hand_bone_name,
                        weight=1.0
                    )
        
        return targets
    
    def set_enabled(self, enabled: bool):
        """Enable or disable hand IK.
        
        Args:
            enabled: Whether hand IK is active
        """
        self.enabled = enabled
        if not enabled:
            self._last_targets = {}  # Clear cached targets
    
    def set_reach_distance(self, distance: float):
        """Set maximum reach distance for hands.
        
        Args:
            distance: Maximum reach in world units
        """
        self.reach_distance = max(0.1, distance)
