"""Combat camera with target framing."""

import math
from typing import Any, Optional
from panda3d.core import LVector3f
from engine.rendering.exploration_camera import ExplorationCamera
from engine.rendering.base_camera import CameraUpdateContext


class CombatCamera(ExplorationCamera):
    """Combat-focused camera with soft-lock target framing.
    
    Extends ExplorationCamera with:
    - Target framing: positions camera to show both player and target
    - FOV widening for situational awareness
    - Smooth target transitions
    
    When no target is set, behaves identically to ExplorationCamera.
    """
    
    def __init__(self, camera_node: Any, sensitivity: float = 40.0,
                 collision_traverser: Optional[Any] = None, 
                 render_node: Optional[Any] = None,
                 side_offset: float = 0.5):
        """Initialize combat camera.
        
        Args:
            camera_node: Panda3D camera NodePath (base.camera)
            sensitivity: Mouse sensitivity for rotation
            collision_traverser: Optional CollisionTraverser for terrain collision
            render_node: Optional render root node for raycasting
            side_offset: Lateral offset (reduced from exploration for better framing)
        """
        super().__init__(camera_node, sensitivity, collision_traverser, 
                        render_node, side_offset)
        
        # Combat-specific parameters
        self.fov_multiplier = 1.2  # Widen FOV for situational awareness
        self.framing_distance_multiplier = 1.3  # Pull back to show both entities
    
    def update(self, ctx: CameraUpdateContext) -> None:
        """Update camera with combat framing if target is set.
        
        Args:
            ctx: Camera update context
        """
        # If no target, use standard exploration behavior
        if ctx.camera_state.target_entity is None:
            super().update(ctx)
            return
            
        # Get target transform
        from engine.components.core import Transform
        target_transform = ctx.world.get_component(ctx.camera_state.target_entity, Transform)
        
        if not target_transform:
             # Target lost/destroyed - verify in next frame or let mechanic handle it
             # For now, fallback to exploration
             super().update(ctx)
             return
             
        # Calculate vector to target
        to_target = target_transform.position - ctx.target_position
        dist = to_target.length()
        
        # Calculate desired yaw (player facing target)
        # atan2(y, x) gives angle from X axis.
        # In Panda3D, Heading is rotation around Z axis. +X is East, +Y is North.
        # atan2(x, y) usually gives angle from North (+Y).
        if dist > 0.1:
            target_heading = math.degrees(math.atan2(-to_target.x, to_target.y))
            
            # Smoothly interpolate yaw to face target
            # Simple lerp for now, could use shortest arc
            yaw_diff = target_heading - ctx.camera_state.yaw
            while yaw_diff > 180: yaw_diff -= 360
            while yaw_diff < -180: yaw_diff += 360
            
            # Strong locking for combat
            ctx.camera_state.yaw += yaw_diff * 10.0 * ctx.dt
            
            # Auto-adjust pitch based on distance (look down if close, up if far)
            # This is simple; maybe refine later
            target_pitch = -10.0 - (5.0 / max(1.0, dist)) 
            ctx.camera_state.pitch += (target_pitch - ctx.camera_state.pitch) * 5.0 * ctx.dt
            
        super().update(ctx)
    
    def on_enter(self, camera_state: Any) -> None:
        """Called when entering combat mode.
        
        Args:
            camera_state: CameraState component
        """
        super().on_enter(camera_state)
        # Future: Apply FOV widening
    
    def on_exit(self, camera_state: Any) -> None:
        """Called when exiting combat mode.
        
        Args:
            camera_state: CameraState component
        """
        super().on_exit(camera_state)
        # Future: Reset FOV to normal
