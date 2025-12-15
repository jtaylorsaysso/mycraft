from dataclasses import dataclass
from typing import Callable, Optional, Protocol, Any


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


def apply_gravity(state: KinematicState, dt: float, gravity: float = -9.81, max_fall_speed: Optional[float] = None) -> None:
    """Apply gravity to the vertical velocity.

    Does not move the entity; use integrate_vertical() after this
    to actually apply the movement and handle ground collisions.
    """

    state.velocity_y += gravity * dt

    if max_fall_speed is not None and state.velocity_y < max_fall_speed:
        state.velocity_y = max_fall_speed


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
        ground_check: Function returning height of ground at entity's position.
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

    # 2. Vertical Movement (Y)
    entity.y += state.velocity_y * dt

    # Ask the caller where the ground is for this entity, if any
    ground_y = ground_check(entity)

    if ground_y is not None and entity.y <= ground_y:
        # Snap to ground and stop falling
        entity.y = ground_y
        state.velocity_y = 0.0
        state.grounded = True
        state.time_since_grounded = 0.0
    else:
        state.grounded = False


def simple_flat_ground_check(entity: SupportsY, ground_height: float = 2.0) -> float:
    """Ground check for a flat world at a fixed y-level.

    This mirrors the previous hard-coded check in InputHandler
    (player feet at y=2). It returns the ground height unconditionally
    so integrate_vertical() can do the comparison.
    """

    return ground_height


def perform_jump(state: KinematicState, jump_height: float) -> None:
    """Set vertical velocity for an instant jump.

    This keeps behavior identical to the current implementation,
    which directly sets velocity_y to jump_height when jumping.
    """

    state.velocity_y = jump_height
    state.grounded = False
    # After performing a jump, clear any buffered jump request.
    state.time_since_jump_pressed = 999.0


def raycast_ground_height(
    entity: Any,
    max_distance: float = 5.0,
    foot_offset: float = 0.2,
    ray_origin_offset: Optional[float] = None,
    ignore: Optional[list] = None,
) -> Optional[float]:
    """Return the ground y-position below an Ursina Entity using raycast.

    This expects an Ursina Entity-like object with a world_position attribute.
    It casts a ray straight down from just above the entity and, if it hits
    something, returns the y-position where the entity's origin should be
    placed so that its feet (offset by foot_offset) rest on the surface.
    """

    try:
        from ursina import Vec3, raycast  # type: ignore
    except Exception:
        # If Ursina is not available, fall back to no ground detected.
        return None

    # Start the ray some distance above the entity to reduce the
    # chance of starting below the terrain when falling fast.
    # For a ~2-unit tall player, 2.0 units above is sufficient.
    if ray_origin_offset is None:
        ray_origin_offset = 2.0

    origin = entity.world_position + Vec3(0, ray_origin_offset, 0)
    direction = Vec3(0, -1, 0)

    ignore_list = ignore or [entity]
    hit_info = raycast(origin, direction, distance=max_distance, ignore=ignore_list)

    if not getattr(hit_info, "hit", False):
        return None

    # Place the entity so that its feet (origin - foot_offset) rest on the hit.
    return hit_info.point.y + foot_offset


def raycast_wall_check(
    entity: Any,
    movement: tuple[float, float, float],
    distance_buffer: float = 0.5,
    ignore: Optional[list] = None
) -> bool:
    """Check if moving by 'movement' would hit a wall.
    
    This casts a ray in the direction of movement.
    """
    try:
        from ursina import Vec3, raycast
    except Exception:
        return False
        
    move_vec = Vec3(*movement)
    dist = move_vec.length()
    
    if dist < 0.001:
        return False
        
    direction = move_vec.normalized()
    origin = entity.world_position + Vec3(0, 1.0, 0) # Cast from center mass/head height
    
    # Check slightly further than we are moving to prevent getting too close
    check_dist = dist + distance_buffer 
    
    ignore_list = ignore or [entity]
    hit_info = raycast(origin, direction, distance=check_dist, ignore=ignore_list)
    
    return hit_info.hit


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
