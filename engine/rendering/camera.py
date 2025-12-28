"""First-person camera controller for Panda3D."""

from panda3d.core import LVector3f
from typing import Optional, Any


class FPSCamera:
    """First-person camera controller using Panda3D."""
    
    def __init__(self, camera_node: Any, player_entity: Any, sensitivity: float = 40.0):
        """Initialize FPS Camera.
        
        Args:
            camera_node: Panda3D camera NodePath (base.camera)
            player_entity: The player entity/node to control
            sensitivity: Mouse sensitivity
        """
        self.camera = camera_node
        self.player = player_entity
        self.sensitivity = sensitivity
        self.clamp_vertical = True
        self.min_pitch = -89.0
        self.max_pitch = 89.0
        
    def update(self, mouse_dx: float, mouse_dy: float, camera_state: Any, dt: float) -> None:
        """Update camera rotation based on mouse movement.
        
        Args:
            mouse_dx: Mouse delta X (horizontal movement) - already per-frame
            mouse_dy: Mouse delta Y (vertical movement) - already per-frame
            camera_state: CameraState component (for reading/writing rotation)
            dt: Delta time (not used for mouse input, which is already per-frame)
        """
        # Horizontal rotation (yaw)
        # NOTE: mouse_dx is already a per-frame delta, don't multiply by dt!
        camera_state.yaw += mouse_dx * self.sensitivity
        
        # Vertical rotation (pitch)
        camera_state.pitch -= mouse_dy * self.sensitivity
        
        # Clamp vertical rotation
        if self.clamp_vertical:
            camera_state.pitch = max(self.min_pitch, min(self.max_pitch, camera_state.pitch))
        
        # Apply rotations to camera
        # Panda3D uses HPR (Heading, Pitch, Roll)
        self.camera.setHpr(camera_state.yaw, camera_state.pitch, 0)
        
    def set_sensitivity(self, value: float) -> None:
        """Update mouse sensitivity."""
        self.sensitivity = value


class ThirdPersonCamera:
    """Third-person camera that orbits around a target entity."""
    
    def __init__(self, camera_node: Any, target_entity: Any, sensitivity: float = 40.0,
                 collision_traverser: Optional[Any] = None, render_node: Optional[Any] = None,
                 side_offset: float = 1.0):
        """Initialize third-person camera.
        
        Args:
            camera_node: Panda3D camera NodePath (base.camera)
            target_entity: The entity/node to orbit around
            sensitivity: Mouse sensitivity for rotation
            collision_traverser: Optional CollisionTraverser for terrain collision
            render_node: Optional render root node for raycasting
            side_offset: Lateral offset for over-the-shoulder view (positive = right)
        """
        self.camera = camera_node
        self.target = target_entity
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
        
    def update(self, mouse_dx: float, mouse_dy: float, dt: float, target_position: LVector3f, 
               camera_state: Any, player_velocity: Optional[LVector3f] = None) -> None:
        """Update camera position and rotation.
        
        Args:
            mouse_dx: Mouse delta X (horizontal movement)
            mouse_dy: Mouse delta Y (vertical movement)
            dt: Delta time
            target_position: World position of the target entity
            camera_state: CameraState component (for reading/writing state)
            player_velocity: Optional player velocity for camera bob
        """
        # Update rotation from mouse input
        # NOTE: mouse_dx/dy are already per-frame deltas, don't multiply by dt!
        camera_state.yaw += mouse_dx * self.sensitivity
        camera_state.pitch -= mouse_dy * self.sensitivity
        
        # Clamp pitch
        camera_state.pitch = max(self.min_pitch, min(self.max_pitch, camera_state.pitch))
        
        # Calculate desired camera position (orbit around target)
        import math
        yaw_rad = math.radians(camera_state.yaw)
        pitch_rad = math.radians(camera_state.pitch)
        
        # Check for collision and adjust distance
        safe_distance = self._calculate_collision_distance(target_position, yaw_rad, pitch_rad, camera_state.distance)
        
        # Smoothly interpolate current_distance toward safe_distance
        camera_state.current_distance += (safe_distance - camera_state.current_distance) * (dt * self.distance_lerp_speed)
        
        # Offset from target using collision-adjusted distance
        offset_x = camera_state.current_distance * math.sin(yaw_rad) * math.cos(pitch_rad)
        offset_y = -camera_state.current_distance * math.cos(yaw_rad) * math.cos(pitch_rad)
        offset_z = camera_state.current_distance * math.sin(pitch_rad) + self.height_offset
        
        # Add lateral offset for over-the-shoulder view
        # Calculate right vector (perpendicular to camera direction in horizontal plane)
        # Right = rotate camera direction 90° clockwise
        right_x = -math.sin(yaw_rad + math.pi / 2)
        right_y = -math.cos(yaw_rad + math.pi / 2)
        
        offset_x += right_x * self.side_offset
        offset_y += right_y * self.side_offset
        
        # Calculate camera bob offset
        bob_offset = self._calculate_bob_offset(player_velocity, camera_state, dt) if player_velocity else (0, 0)
        
        desired_pos = target_position + LVector3f(offset_x + bob_offset[0], offset_y, offset_z + bob_offset[1])
        
        # Constrain camera to stay above ground
        if self.collision_traverser and self.render_node:
            terrain_height = self._get_terrain_height_at(desired_pos.x, desired_pos.y)
            if terrain_height is not None:
                min_z = terrain_height + self.min_camera_height_above_ground
                if desired_pos.z < min_z:
                    desired_pos.z = min_z
        
        # Smooth camera movement (lerp)
        current_pos = self.camera.getPos()
        new_pos = current_pos + (desired_pos - current_pos) * (dt * self.lerp_speed)
        
        self.camera.setPos(new_pos)
        
        # Look at target (with height offset for better framing)
        look_at_target = target_position + LVector3f(0, 0, self.height_offset * 0.5)
        self.camera.lookAt(look_at_target)
    
    def _calculate_collision_distance(self, target_pos: LVector3f, yaw_rad: float, pitch_rad: float, desired_distance: float) -> float:
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
        
        from panda3d.core import CollisionRay, CollisionNode, CollisionHandlerQueue, BitMask32, LPoint3f
        import math
        
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
        
        from panda3d.core import CollisionRay, CollisionNode, CollisionHandlerQueue, BitMask32, LPoint3f
        
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
    
    def _calculate_bob_offset(self, player_velocity: LVector3f, camera_state: Any, dt: float) -> tuple[float, float]:
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
        
        import math
        
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
    
    def set_sensitivity(self, value: float) -> None:
        """Update mouse sensitivity."""
        self.sensitivity = value
    
    def set_distance(self, camera_state: Any, distance: float) -> None:
        """Update orbit distance in CameraState.
        
        Args:
            camera_state: CameraState component
            distance: New distance value
        """
        camera_state.distance = max(self.min_distance, min(self.max_distance, distance))
