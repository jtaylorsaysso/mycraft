"""Exploration camera with orbit control and auto-centering."""

import math
from typing import Any, Optional
from panda3d.core import LVector3f, LPoint3f, CollisionRay, CollisionNode, CollisionHandlerQueue, BitMask32
from engine.rendering.base_camera import BaseCamera, CameraUpdateContext


class ExplorationCamera(BaseCamera):
    """Third-person exploration camera with soft auto-centering.
    
    Features:
    - Orbit camera with yaw/pitch rotation
    - Soft auto-centering: camera drifts behind player when moving
    - Terrain collision detection (raycast pull-in)
    - Camera bob during movement
    - Scroll wheel zoom
    - Over-the-shoulder offset
    - Ground height constraints
    """
    
    def __init__(self, camera_node: Any, sensitivity: float = 40.0,
                 collision_traverser: Optional[Any] = None, 
                 render_node: Optional[Any] = None,
                 side_offset: float = 1.0):
        """Initialize exploration camera.
        
        Args:
            camera_node: Panda3D camera NodePath (base.camera)
            sensitivity: Mouse sensitivity for rotation
            collision_traverser: Optional CollisionTraverser for terrain collision
            render_node: Optional render root node for raycasting
            side_offset: Lateral offset for over-the-shoulder view (positive = right)
        """
        self.camera = camera_node
        self.sensitivity = sensitivity
        
        # Collision detection
        self.collision_traverser = collision_traverser
        self.render_node = render_node
        self.collision_offset = 0.3  # Safety margin to prevent clipping
        
        # Camera orbit parameters (constants)
        self.height_offset = 2.0  # Height above player
        self.side_offset = side_offset  # Lateral offset for over-the-shoulder view
        self.min_distance = 1.5  # Minimum distance (for collision)
        self.max_distance = 10.0
        self.min_pitch = -60.0  # Don't look too far down
        self.max_pitch = 60.0  # Don't look too far up
        
        # Smoothing (constants)
        self.lerp_speed = 8.0  # How fast camera follows target
        self.distance_lerp_speed = 10.0  # How fast distance adjusts for collision
        
        # Camera bob parameters (constants)
        self.bob_enabled = True
        self.bob_frequency = 2.5  # Hz (cycles per second)
        self.bob_amplitude_x = 0.05  # Horizontal bob amount
        self.bob_amplitude_z = 0.03  # Vertical bob amount
        self.bob_speed_threshold = 0.1  # Minimum speed for bob to activate
        
        # Ground constraints
        self.min_camera_height_above_ground = 0.5  # Minimum clearance above terrain
        
        # Auto-centering
        self.auto_center_dead_zone = 0.5  # Seconds after mouse input before auto-center activates
    
    def update(self, ctx: CameraUpdateContext) -> None:
        """Update camera position and orientation.
        
        Args:
            ctx: Camera update context
        """
        # Track mouse movement for auto-center dead zone
        if ctx.mouse_delta != (0, 0):
            ctx.camera_state.mouse_moved_recently = self.auto_center_dead_zone
        else:
            ctx.camera_state.mouse_moved_recently = max(0, 
                ctx.camera_state.mouse_moved_recently - ctx.dt)
        
        # Update rotation from mouse input
        # NOTE: mouse_dx/dy are already per-frame deltas, don't multiply by dt!
        ctx.camera_state.yaw += ctx.mouse_delta[0] * self.sensitivity
        ctx.camera_state.pitch -= ctx.mouse_delta[1] * self.sensitivity
        
        # Apply auto-centering if conditions are met
        self._apply_auto_center(ctx)
        
        # Clamp pitch
        ctx.camera_state.pitch = max(self.min_pitch, 
                                     min(self.max_pitch, ctx.camera_state.pitch))
        
        # Calculate desired camera position (orbit around target)
        yaw_rad = math.radians(ctx.camera_state.yaw)
        pitch_rad = math.radians(ctx.camera_state.pitch)
        
        # Check for collision and adjust distance
        safe_distance = self._calculate_collision_distance(
            ctx.target_position, yaw_rad, pitch_rad, ctx.camera_state.distance
        )
        
        # Smoothly interpolate current_distance toward safe_distance
        ctx.camera_state.current_distance += (
            (safe_distance - ctx.camera_state.current_distance) * 
            (ctx.dt * self.distance_lerp_speed)
        )
        
        # Offset from target using collision-adjusted distance
        offset_x = ctx.camera_state.current_distance * math.sin(yaw_rad) * math.cos(pitch_rad)
        offset_y = -ctx.camera_state.current_distance * math.cos(yaw_rad) * math.cos(pitch_rad)
        offset_z = ctx.camera_state.current_distance * math.sin(pitch_rad) + self.height_offset
        
        # Add lateral offset for over-the-shoulder view
        # Calculate right vector (perpendicular to camera direction in horizontal plane)
        # Right = rotate camera direction 90° clockwise
        right_x = -math.sin(yaw_rad + math.pi / 2)
        right_y = -math.cos(yaw_rad + math.pi / 2)
        
        offset_x += right_x * self.side_offset
        offset_y += right_y * self.side_offset
        
        # Calculate camera bob offset
        bob_offset = self._calculate_bob_offset(ctx.player_velocity, ctx.camera_state, ctx.dt)
        
        desired_pos = ctx.target_position + LVector3f(
            offset_x + bob_offset[0], 
            offset_y, 
            offset_z + bob_offset[1]
        )
        
        # Constrain camera to stay above ground
        if self.collision_traverser and self.render_node:
            terrain_height = self._get_terrain_height_at(desired_pos.x, desired_pos.y)
            if terrain_height is not None:
                min_z = terrain_height + self.min_camera_height_above_ground
                if desired_pos.z < min_z:
                    desired_pos.z = min_z
        
        # Smooth camera movement (lerp)
        current_pos = self.camera.getPos()
        new_pos = current_pos + (desired_pos - current_pos) * (ctx.dt * self.lerp_speed)
        
        self.camera.setPos(new_pos)
        
        # Look at target (with height offset for better framing)
        look_at_target = ctx.target_position + LVector3f(0, 0, self.height_offset * 0.5)
        self.camera.lookAt(look_at_target)
    
    def _apply_auto_center(self, ctx: CameraUpdateContext) -> None:
        """Apply soft auto-centering to camera yaw.
        
        When player is moving without recent mouse input, camera
        gradually rotates to face behind the player's movement direction.
        
        Args:
            ctx: Camera update context
        """
        # Check if auto-centering should be active
        speed = math.sqrt(ctx.player_velocity.x**2 + ctx.player_velocity.y**2)
        
        if (speed > 0.1 and 
            ctx.camera_state.mouse_moved_recently <= 0 and
            ctx.camera_state.auto_center_strength > 0):
            
            # Calculate player facing direction from velocity
            player_heading = math.degrees(math.atan2(ctx.player_velocity.x, 
                                                     ctx.player_velocity.y))
            
            # Target yaw is behind player (180° from facing direction)
            target_yaw = player_heading + 180
            
            # Normalize angle difference to [-180, 180]
            yaw_diff = target_yaw - ctx.camera_state.yaw
            while yaw_diff > 180:
                yaw_diff -= 360
            while yaw_diff < -180:
                yaw_diff += 360
            
            # Smoothly rotate toward target yaw
            ctx.camera_state.yaw += (yaw_diff * 
                ctx.camera_state.auto_center_strength * ctx.dt)
                
            # Pitch Auto-Center
            # Gently drift pitch back to optimal viewing angle (e.g. -15 degrees)
            # This prevents "overhead views hanging there"
            target_pitch = -15.0
            pitch_diff = target_pitch - ctx.camera_state.pitch
            
            # Use same strength
            ctx.camera_state.pitch += (pitch_diff * 
                ctx.camera_state.auto_center_strength * ctx.dt)
    
    def _calculate_collision_distance(self, target_pos: LVector3f, yaw_rad: float, 
                                      pitch_rad: float, desired_distance: float) -> float:
        """Calculate safe camera distance considering terrain collision.
        
        Raycasts from player toward camera position. If terrain blocks the view,
        returns a shorter distance to prevent clipping.
        
        Args:
            target_pos: Player position
            yaw_rad: Camera yaw in radians
            pitch_rad: Camera pitch in radians
            desired_distance: Desired camera distance from CameraState
            
        Returns:
            Safe distance (clamped between min_distance and desired_distance)
        """
        # If no collision system available, use desired distance
        if self.collision_traverser is None or self.render_node is None:
            return desired_distance
        
        # Calculate direction from player to desired camera position
        dir_x = math.sin(yaw_rad) * math.cos(pitch_rad)
        dir_y = -math.cos(yaw_rad) * math.cos(pitch_rad)
        dir_z = math.sin(pitch_rad)
        
        # Start ray from player position (with height offset for better results)
        ray_origin = LPoint3f(target_pos.x, target_pos.y, target_pos.z + self.height_offset)
        ray_direction = LVector3f(dir_x, dir_y, dir_z)
        
        # Create collision ray
        ray = CollisionRay()
        ray.setOrigin(ray_origin)
        ray.setDirection(ray_direction)
        
        # Create temporary collision node
        ray_node = CollisionNode('camera_collision_ray')
        ray_node.addSolid(ray)
        ray_node.setFromCollideMask(BitMask32.bit(1))  # Collide with terrain
        ray_node.setIntoCollideMask(BitMask32.allOff())
        
        # Attach to scene graph
        ray_np = self.render_node.attachNewNode(ray_node)
        
        # Perform collision check
        handler = CollisionHandlerQueue()
        self.collision_traverser.addCollider(ray_np, handler)
        self.collision_traverser.traverse(self.render_node)
        
        # Calculate safe distance
        safe_distance = desired_distance
        
        if handler.getNumEntries() > 0:
            handler.sortEntries()
            entry = handler.getEntry(0)
            hit_point = entry.getSurfacePoint(self.render_node)
            
            # Calculate distance from player to hit point
            hit_distance = (hit_point - ray_origin).length()
            
            # If hit is closer than desired distance, pull camera in
            if hit_distance < desired_distance:
                # Apply safety offset to prevent clipping
                safe_distance = max(self.min_distance, hit_distance - self.collision_offset)
        
        # Clean up
        self.collision_traverser.removeCollider(ray_np)
        ray_np.removeNode()
        
        return safe_distance
    
    def _get_terrain_height_at(self, x: float, y: float) -> Optional[float]:
        """Get terrain height at XY position using downward raycast.
        
        Args:
            x: World X coordinate
            y: World Y coordinate (Panda3D depth)
            
        Returns:
            Terrain Z coordinate, or None if no terrain found
        """
        if self.collision_traverser is None or self.render_node is None:
            return None
        
        # Cast ray from high above straight down
        ray_origin = LPoint3f(x, y, 100.0)  # Start well above any terrain
        ray_direction = LVector3f(0, 0, -1)  # Straight down
        
        # Create collision ray
        ray = CollisionRay()
        ray.setOrigin(ray_origin)
        ray.setDirection(ray_direction)
        
        # Create temporary collision node
        ray_node = CollisionNode('terrain_height_ray')
        ray_node.addSolid(ray)
        ray_node.setFromCollideMask(BitMask32.bit(1))  # Collide with terrain
        ray_node.setIntoCollideMask(BitMask32.allOff())
        
        # Attach to scene graph
        ray_np = self.render_node.attachNewNode(ray_node)
        
        # Perform collision check
        handler = CollisionHandlerQueue()
        self.collision_traverser.addCollider(ray_np, handler)
        self.collision_traverser.traverse(self.render_node)
        
        # Get terrain height
        terrain_height = None
        if handler.getNumEntries() > 0:
            handler.sortEntries()
            entry = handler.getEntry(0)
            hit_point = entry.getSurfacePoint(self.render_node)
            terrain_height = hit_point.z
        
        # Clean up
        self.collision_traverser.removeCollider(ray_np)
        ray_np.removeNode()
        
        return terrain_height
    
    def _calculate_bob_offset(self, player_velocity: LVector3f, 
                              camera_state: Any, dt: float) -> tuple[float, float]:
        """Calculate camera bob offset based on player movement.
        
        Args:
            player_velocity: Player's current velocity vector
            camera_state: CameraState component (for reading/writing bob_time)
            dt: Delta time
            
        Returns:
            Tuple of (horizontal_offset, vertical_offset)
        """
        if not self.bob_enabled:
            return (0.0, 0.0)
        
        # Calculate horizontal speed (ignore vertical)
        speed = math.sqrt(player_velocity.x**2 + player_velocity.y**2)
        
        # Only bob if moving above threshold
        if speed < self.bob_speed_threshold:
            camera_state.bob_time = 0.0  # Reset when stationary
            return (0.0, 0.0)
        
        # Advance bob time
        camera_state.bob_time += dt
        
        # Calculate bob offsets using sine waves
        # Horizontal bob (side-to-side)
        bob_x = math.sin(camera_state.bob_time * self.bob_frequency * 2 * math.pi) * self.bob_amplitude_x
        
        # Vertical bob (up-down) - use abs to create bounce effect
        bob_z = abs(math.sin(camera_state.bob_time * self.bob_frequency * 2 * 2 * math.pi)) * self.bob_amplitude_z
        
        # Scale by speed (faster movement = more bob)
        speed_factor = min(speed / 5.0, 1.0)  # Cap at speed 5
        
        return (bob_x * speed_factor, bob_z * speed_factor)
    
    def on_enter(self, camera_state: Any) -> None:
        """Called when entering exploration mode.
        
        Resets current_distance to match target distance to fix zoom bug.
        
        Args:
            camera_state: CameraState component
        """
        # Reset current_distance to match target distance
        # This fixes zoom bug after mode toggle
        camera_state.current_distance = camera_state.distance
    
    def set_sensitivity(self, value: float) -> None:
        """Update mouse sensitivity.
        
        Args:
            value: New sensitivity value
        """
        self.sensitivity = value
    
    def set_distance(self, camera_state: Any, distance: float) -> None:
        """Update orbit distance in CameraState.
        
        Args:
            camera_state: CameraState component
            distance: New distance value
        """
        camera_state.distance = max(self.min_distance, min(self.max_distance, distance))
