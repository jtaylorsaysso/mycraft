from dataclasses import dataclass
from typing import Callable, Optional, Protocol, Any, Tuple
from panda3d.core import LVector3f, CollisionRay, CollisionNode, CollisionTraverser, CollisionHandlerQueue, BitMask32


class SupportsY(Protocol):
    """Protocol for entities that have a mutable y-position.

    This matches Ursina's Entity interface enough for our purposes
    without importing Ursina here.
    """

    y: float


@dataclass
class KinematicState:
    """Shared vertical-physics state for kinematic entities.

    This is intentionally minimal so it can be reused by multiple
    controllers (player, NPCs, etc.).
    """

    velocity_y: float = 0.0
    velocity_x: float = 0.0
    velocity_z: float = 0.0
    grounded: bool = True
    # Time since we were last on the ground. Used for coyote time.
    time_since_grounded: float = 0.0
    # Time since jump was last requested. Used for jump buffering.
    time_since_jump_pressed: float = 999.0

    # Slope physics
    sliding: bool = False
    surface_normal: Tuple[float, float, float] = (0, 1, 0)  # Y-up by default
    slope_angle: float = 0.0  # degrees


def apply_gravity(state: KinematicState, dt: float, gravity: float = -9.81, max_fall_speed: Optional[float] = None) -> None:
    """Apply gravity to the vertical velocity.

    Does not move the entity; use integrate_vertical() after this
    to actually apply the movement and handle ground collisions.
    """

    state.velocity_y += gravity * dt

    if max_fall_speed is not None and state.velocity_y < max_fall_speed:
        state.velocity_y = max_fall_speed


def apply_horizontal_acceleration(
    state: KinematicState,
    target_vel: tuple[float, float],
    dt: float,
    grounded: bool,
) -> None:
    """Smoothly accelerate/decelerate horizontal velocity.

    Args:
        state: The entity's kinematic state.
        target_vel: Desired (x, z) velocity (already clamped to MOVE_SPEED).
        dt: Frame delta time.
        grounded: Whether the entity is on the ground.
    """
    from engine.physics.constants import ACCELERATION, FRICTION, AIR_CONTROL, SLIDE_CONTROL

    # Effective acceleration based on grounded state
    effective_accel = ACCELERATION if grounded else ACCELERATION * AIR_CONTROL

    # Reduce control when sliding
    if state.sliding:
        effective_accel *= SLIDE_CONTROL  # 30% control while sliding

    for axis, name in zip((0, 1), ("x", "z")):
        cur = getattr(state, f"velocity_{name}")
        target = target_vel[axis]
        
        if abs(target) > 0.001:
            # Determine accel rate: use boosted deceleration if turning around
            accel = effective_accel
            if cur * target < 0:
                # Opposing direction: apply boosted deceleration
                accel = max(accel, FRICTION * 2.0)
                
            # Accelerate toward target speed
            if cur < target:
                cur = min(cur + accel * dt, target)
            elif cur > target:
                cur = max(cur - accel * dt, target)
        else:
            # No input – apply friction (decelerate to zero)
            if abs(cur) > 0.001:
                decel = FRICTION
                if cur > 0:
                    cur = max(cur - decel * dt, 0.0)
                else:
                    cur = min(cur + decel * dt, 0.0)
        setattr(state, f"velocity_{name}", cur)


def calculate_slope_angle(normal: Tuple[float, float, float]) -> float:
    """Calculate slope angle in degrees from surface normal.

    Args:
        normal: Surface normal (nx, ny, nz) where y is up

    Returns:
        Angle in degrees (0 = flat, 90 = vertical wall)
    """
    import math
    # Angle between normal and up vector (0, 1, 0)
    # cos(angle) = normal · up = normal.y (since up is unit vector)
    ny = normal[1]
    # Clamp to avoid numerical errors with acos
    ny = max(-1.0, min(1.0, ny))
    angle_rad = math.acos(ny)
    return math.degrees(angle_rad)


def project_velocity_onto_slope(
    velocity: Tuple[float, float, float],
    normal: Tuple[float, float, float]
) -> Tuple[float, float, float]:
    """Project velocity vector onto slope surface.

    Removes the component of velocity perpendicular to the slope,
    keeping only the component parallel to the surface.

    Args:
        velocity: Velocity vector (vx, vy, vz)
        normal: Surface normal (nx, ny, nz)

    Returns:
        Projected velocity (vx', vy', vz')
    """
    vx, vy, vz = velocity
    nx, ny, nz = normal

    # v_projected = v - (v · n) * n
    dot = vx * nx + vy * ny + vz * nz

    return (
        vx - dot * nx,
        vy - dot * ny,
        vz - dot * nz
    )


def get_downslope_direction(normal: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Get the direction of steepest descent on a slope.

    Args:
        normal: Surface normal (nx, ny, nz) where y is up

    Returns:
        Normalized downslope direction vector (horizontal component only)
    """
    import math
    nx, ny, nz = normal

    # The downslope direction is the horizontal component of the normal, negated
    # (negative because we want to go down, and normal points up from surface)
    horiz_x = -nx
    horiz_z = -nz

    length = math.sqrt(horiz_x**2 + horiz_z**2)
    if length < 0.001:
        return (0.0, 0.0, 0.0)  # Flat surface, no downslope

    return (horiz_x / length, 0.0, horiz_z / length)


def get_slope_velocity_component(state: KinematicState) -> Tuple[float, float, float]:
    """Get the velocity component from the slope for jump boosts.

    When jumping off a slope, this gives the velocity boost from the slope's
    orientation, making uphill jumps go higher and downhill jumps go farther.

    Args:
        state: Entity kinematic state with surface normal

    Returns:
        Velocity component (vx, vy, vz) to add to jump
    """
    import math

    # Get the slope's "up" direction (perpendicular to surface, in direction of normal)
    # Scale by current horizontal speed to get the boost
    nx, ny, nz = state.surface_normal

    # Calculate horizontal speed
    horiz_speed = math.sqrt(state.velocity_x**2 + state.velocity_z**2)

    # The slope contribution is proportional to:
    # 1. How steep the slope is (more steep = more vertical component)
    # 2. How fast we're moving horizontally

    # For a slope, the vertical boost is: horiz_speed * tan(angle)
    # But we can compute this from the normal: tan(angle) = sqrt(nx² + nz²) / ny

    if abs(ny) < 0.001:  # Nearly vertical surface
        return (0.0, 0.0, 0.0)

    slope_factor = math.sqrt(nx**2 + nz**2) / ny

    # Direction of movement on slope
    if horiz_speed > 0.001:
        move_dir_x = state.velocity_x / horiz_speed
        move_dir_z = state.velocity_z / horiz_speed
    else:
        return (0.0, 0.0, 0.0)

    # Check if moving uphill or downhill
    # Dot product of movement direction with downslope direction
    downslope = get_downslope_direction(state.surface_normal)
    dot = move_dir_x * downslope[0] + move_dir_z * downslope[2]

    # If moving uphill (dot < 0), add upward velocity
    # If moving downhill (dot > 0), add downward velocity
    vertical_boost = -dot * horiz_speed * slope_factor * 0.5  # 0.5 is tuning factor

    return (0.0, vertical_boost, 0.0)


def apply_slope_forces(state: KinematicState, dt: float) -> None:
    """Apply sliding forces when on steep slopes.

    Uses momentum-based sliding: preserves horizontal velocity and adds
    downslope acceleration, with friction opposing motion.

    Args:
        state: Entity kinematic state
        dt: Delta time
    """
    if not state.sliding:
        return

    from engine.physics.constants import SLIDE_ACCELERATION, SLIDE_FRICTION
    import math

    # Get downslope direction (horizontal only)
    downslope = get_downslope_direction(state.surface_normal)

    # Apply downslope acceleration
    state.velocity_x += downslope[0] * SLIDE_ACCELERATION * dt
    state.velocity_z += downslope[2] * SLIDE_ACCELERATION * dt

    # Apply slide friction (opposes velocity)
    speed = math.sqrt(state.velocity_x**2 + state.velocity_z**2)
    if speed > 0.001:
        # Friction reduces speed proportionally
        friction_reduction = SLIDE_FRICTION * dt
        new_speed = max(0.0, speed - friction_reduction)
        speed_factor = new_speed / speed

        state.velocity_x *= speed_factor
        state.velocity_z *= speed_factor


def integrate_movement(
    entity: Any,
    state: KinematicState,
    dt: float,
    ground_check: Callable[[Any], Optional[float]],
    wall_check: Optional[Callable[[Any, tuple[float, float, float]], bool]] = None
) -> None:
    """Integrate 3D motion and resolve collisions.
    
    Args:
        entity: The entity to move (must have x, y, z, position).
        state: The physics state containing velocity.
        dt: Delta time.
        ground_check: Function returning height or (height, normal) tuple.
        wall_check: Optional function returning True if a move would hit a wall.
                    Signature: (entity, movement_vector) -> hit_wall
    """
    
    # 1. Horizontal Movement (X/Z)
    dx = state.velocity_x * dt
    dz = state.velocity_z * dt
    
    # Simple collision check: try moving, if hit, slide or stop
    # For now, we'll do a simple "try move one axis at a time" approach
    # to allow sliding along walls.
    
    if wall_check:
        # Try full diagonal movement first
        if (dx != 0 or dz != 0) and not wall_check(entity, (dx, 0, dz)):
            # No collision on diagonal movement
            entity.x += dx
            entity.z += dz
        else:
            # Hit a wall on diagonal, try sliding along each axis
            x_blocked = False
            z_blocked = False
            
            # Try X movement
            if dx != 0 and not wall_check(entity, (dx, 0, 0)):
                entity.x += dx
            else:
                x_blocked = True
                # Don't fully stop X velocity - allow some sliding momentum
                state.velocity_x *= 0.5  # Preserve some momentum for sliding
            
            # Try Z movement
            if dz != 0 and not wall_check(entity, (0, 0, dz)):
                entity.z += dz
            else:
                z_blocked = True
                # Don't fully stop Z velocity - allow some sliding momentum
                state.velocity_z *= 0.5  # Preserve some momentum for sliding
            
            # If both axes blocked, fully stop (corner case)
            if x_blocked and z_blocked:
                state.velocity_x = 0
                state.velocity_z = 0
    else:
        # No collision checks, just move
        entity.x += dx
        entity.z += dz

    # 2. Vertical Movement (Y) with slope handling
    entity.y += state.velocity_y * dt

    # Get ground height and surface normal
    ground_result = ground_check(entity)
    
    if ground_result is not None:
        # Check if we got a tuple (height, normal) or just height
        if isinstance(ground_result, tuple):
            ground_y, normal = ground_result
            state.surface_normal = normal
            state.slope_angle = calculate_slope_angle(normal)
        else:
            ground_y = ground_result
            state.surface_normal = (0, 1, 0)
            state.slope_angle = 0.0
        
        if entity.y <= ground_y:
            # Snap to ground
            entity.y = ground_y
            state.velocity_y = 0.0
            state.grounded = True
            state.time_since_grounded = 0.0
            
            # Determine if slope is too steep for walking
            from engine.physics.constants import MAX_WALKABLE_SLOPE
            if state.slope_angle > MAX_WALKABLE_SLOPE:
                state.sliding = True
            else:
                state.sliding = False
        else:
            # In air
            state.grounded = False
            state.sliding = False
            state.surface_normal = (0, 1, 0)
            state.slope_angle = 0.0
    else:
        # No ground detected
        state.grounded = False
        state.sliding = False
        state.surface_normal = (0, 1, 0)
        state.slope_angle = 0.0


def simple_flat_ground_check(entity: SupportsY, ground_height: float = 2.0) -> float:
    """Ground check for a flat world at a fixed y-level.

    This mirrors the previous hard-coded check in InputHandler
    (player feet at y=2). It returns the ground height unconditionally
    so integrate_vertical() can do the comparison.
    """

    return ground_height


def perform_jump(state: KinematicState, jump_height: float) -> None:
    """Set vertical velocity for an instant jump.

    If jumping from a slope, adds the slope's velocity component
    to make uphill jumps go higher and downhill jumps go farther.

    Args:
        state: Kinematic state
        jump_height: Base jump velocity
    """
    # Base jump velocity
    state.velocity_y = jump_height

    # Add slope contribution if on a slope
    if state.grounded and state.slope_angle > 1.0:  # More than 1° slope
        slope_vel = get_slope_velocity_component(state)
        state.velocity_y += slope_vel[1]  # Add vertical component

    state.grounded = False
    # After performing a jump, clear any buffered jump request.
    state.time_since_jump_pressed = 999.0


def raycast_ground_height(
    entity: Any,
    collision_traverser: CollisionTraverser,
    render_node: Any,
    max_distance: float = 5.0,
    foot_offset: float = 0.2,
    ray_origin_offset: float = 2.0,
    ignore: Optional[list] = None,
    return_normal: bool = False
) -> Optional[float] | Optional[Tuple[float, Tuple[float, float, float]]]:
    """Return the ground y-position below an entity using Panda3D collision.

    Casts a ray straight down from above the entity to detect terrain.
    
    Args:
        entity: The entity to raycast from (must have x, y, z attributes)
        collision_traverser: Panda3D CollisionTraverser instance
        render_node: Root render node to traverse against
        max_distance: Maximum raycast distance
        foot_offset: Offset for feet placement
        ray_origin_offset: Height above entity to start ray
        ignore: List of entities to ignore (not yet implemented)
        return_normal: If True, return (height, normal) tuple
    
    Returns:
        Ground Y position, or (height, normal) if return_normal=True, or None if no hit
    """
    from panda3d.core import (
        CollisionRay, CollisionNode, CollisionHandlerQueue, 
        BitMask32, LPoint3f, NodePath
    )
    
    # Create ray from above entity pointing down
    # Entity coordinates: x, y (up), z (depth)
    # Panda3D coordinates: x, y (depth), z (up)
    ray_origin = LPoint3f(entity.x, entity.z, entity.y + ray_origin_offset)
    ray_direction = LVector3f(0, 0, -1)  # Down in Panda3D
    
    ray = CollisionRay()
    ray.setOrigin(ray_origin)
    ray.setDirection(ray_direction)
    
    # Create temporary collision node for ray
    ray_node = CollisionNode('ground_ray')
    ray_node.addSolid(ray)
    ray_node.setFromCollideMask(BitMask32.bit(1))  # Collide with terrain layer
    ray_node.setIntoCollideMask(BitMask32.allOff())  # Ray itself is not collidable
    
    # Create temporary NodePath for the ray
    ray_np = NodePath(ray_node)
    
    # Traverse and check for collisions
    handler = CollisionHandlerQueue()
    collision_traverser.addCollider(ray_np, handler)
    collision_traverser.traverse(render_node)
    
    # Get closest hit
    if handler.getNumEntries() > 0:
        handler.sortEntries()
        entry = handler.getEntry(0)
        hit_point = entry.getSurfacePoint(render_node)
        
        # Clean up - remove the temporary collider
        collision_traverser.removeCollider(ray_np)
        
        if return_normal:
            # Get surface normal from collision
            normal = entry.getSurfaceNormal(render_node)
            return (hit_point.z + foot_offset, (normal.x, normal.y, normal.z))
        else:
            # Return height with foot offset (convert Panda3D Z to entity Y)
            return hit_point.z + foot_offset
    
    # Clean up even if no hit
    collision_traverser.removeCollider(ray_np)
    return None


def raycast_wall_check(
    entity: Any,
    movement: tuple[float, float, float],
    collision_traverser: CollisionTraverser,
    render_node: Any,
    distance_buffer: float = 0.5,
    ignore: Optional[list] = None
) -> bool:
    """Check if moving by 'movement' would hit a wall using Panda3D collision.
    
    Casts a ray in the direction of movement to detect obstacles.
    
    Args:
        entity: The entity to check from
        movement: Movement vector (dx, dy, dz) where dy is vertical, dx/dz are horizontal
        collision_traverser: Panda3D CollisionTraverser instance
        render_node: Root render node to traverse against
        distance_buffer: Extra distance to check beyond movement
        ignore: List of entities to ignore (not yet implemented)
    
    Returns:
        True if wall hit, False otherwise
    """
    from panda3d.core import (
        CollisionRay, CollisionNode, CollisionHandlerQueue,
        BitMask32, LPoint3f, NodePath
    )
    import math
    
    dx, dy, dz = movement
    
    # Skip if no horizontal movement
    if abs(dx) < 0.001 and abs(dz) < 0.001:
        return False
    
    # Create ray from entity in movement direction
    # Ray at mid-height of entity
    ray_origin = LPoint3f(entity.x, entity.z, entity.y + 0.9)  # Mid-height
    
    # Normalize movement direction (horizontal only)
    length = math.sqrt(dx*dx + dz*dz)
    # Convert to Panda3D coordinates: (dx, dz, 0) -> (dx, dz, 0)
    direction = LVector3f(dx/length, dz/length, 0)
    
    ray = CollisionRay()
    ray.setOrigin(ray_origin)
    ray.setDirection(direction)
    
    # Create temporary collision node
    ray_node = CollisionNode('wall_ray')
    ray_node.addSolid(ray)
    ray_node.setFromCollideMask(BitMask32.bit(1))  # Collide with terrain
    ray_node.setIntoCollideMask(BitMask32.allOff())
    
    ray_np = NodePath(ray_node)
    
    # Traverse and check for collisions
    handler = CollisionHandlerQueue()
    collision_traverser.addCollider(ray_np, handler)
    collision_traverser.traverse(render_node)
    
    # Check if hit within movement distance + buffer
    hit_wall = False
    if handler.getNumEntries() > 0:
        handler.sortEntries()
        entry = handler.getEntry(0)
        hit_point = entry.getSurfacePoint(render_node)
        
        # Calculate distance to hit
        hit_distance = (hit_point - ray_origin).length()
        
        # Check if hit is within movement range
        if hit_distance < (length + distance_buffer):
            hit_wall = True
    
    # Clean up
    collision_traverser.removeCollider(ray_np)
    
    return hit_wall


def update_timers(state: KinematicState, dt: float) -> None:
    """Advance coyote-time and jump-buffer timers.

    Call this once per frame after integrate_vertical() so that
    grounded state is up to date.
    """

    if state.grounded:
        state.time_since_grounded = 0.0
    else:
        state.time_since_grounded += dt

    state.time_since_jump_pressed += dt


def register_jump_press(state: KinematicState) -> None:
    """Record that the player has requested a jump this frame."""

    state.time_since_jump_pressed = 0.0


def can_consume_jump(
    state: KinematicState,
    coyote_time: float = 0.15,
    jump_buffer_time: float = 0.15,
) -> bool:
    """Return True if a buffered jump should be performed now.

    A jump is allowed if:
    - We have requested a jump recently (within jump_buffer_time), and
    - We have been on the ground recently (within coyote_time).
    """

    return (
        state.time_since_jump_pressed <= jump_buffer_time
        and state.time_since_grounded <= coyote_time
    )
