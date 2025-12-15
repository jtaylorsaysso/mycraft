"""Debug visualization for collision system.

Provides visual feedback for raycasts, hitboxes, and collision points
to help debug and tune collision behavior during playtesting.
"""

from typing import Optional
from ursina import Entity, Vec3, color, destroy


class CollisionDebugRenderer:
    """Renders visual debug information for collision system."""
    
    def __init__(self):
        self.enabled = False
        self._raycast_lines = []
        self._hit_points = []
        self._hitbox = None
        
    def toggle(self) -> bool:
        """Toggle debug rendering on/off. Returns new state."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.clear()
        return self.enabled
    
    def clear(self):
        """Remove all debug visualization entities."""
        for line in self._raycast_lines:
            destroy(line)
        for point in self._hit_points:
            destroy(point)
        if self._hitbox:
            destroy(self._hitbox)
        
        self._raycast_lines = []
        self._hit_points = []
        self._hitbox = None
    
    def draw_raycast(
        self,
        origin: Vec3,
        direction: Vec3,
        distance: float,
        hit: bool,
        debug_color: Optional[tuple] = None
    ):
        """Draw a raycast line for debugging.
        
        Args:
            origin: Starting point of the ray
            direction: Normalized direction vector
            distance: Maximum distance of the ray
            hit: Whether the ray hit something
            debug_color: Optional RGB tuple for line color
        """
        if not self.enabled:
            return
        
        # Calculate endpoint
        end = origin + direction * distance
        
        # Choose color based on hit status
        if debug_color:
            line_color = color.rgb(*debug_color)
        else:
            line_color = color.green if hit else color.red
        
        # Create line entity
        # Using a simple approach: create a thin box between origin and end
        midpoint = (origin + end) / 2
        length = distance
        
        line = Entity(
            model='cube',
            position=midpoint,
            scale=(0.05, 0.05, length),
            color=line_color,
            alpha=0.5,
            rotation=Vec3(0, 0, 0),  # Will need proper rotation calculation
            unlit=True
        )
        
        # Point the line in the direction of the ray
        # For now, only support vertical (downward) rays for ground detection
        if direction.y < -0.9:  # Downward ray
            line.scale = (0.05, length, 0.05)
        
        self._raycast_lines.append(line)
    
    def draw_hit_point(self, position: Vec3, normal: Optional[Vec3] = None):
        """Draw a visual indicator at a raycast hit point.
        
        Args:
            position: World position where the ray hit
            normal: Optional surface normal at hit point
        """
        if not self.enabled:
            return
        
        # Create a small sphere at the hit point
        point = Entity(
            model='sphere',
            position=position,
            scale=0.2,
            color=color.yellow,
            unlit=True
        )
        
        self._hit_points.append(point)
    
    def draw_hitbox(
        self,
        entity,
        width: float,
        height: float,
        depth: float,
        debug_color: Optional[tuple] = None
    ):
        """Draw a wireframe box showing the player's collision bounds.
        
        Args:
            entity: The entity to draw the hitbox around
            width: Width of the hitbox (X axis)
            height: Height of the hitbox (Y axis)
            depth: Depth of the hitbox (Z axis)
            debug_color: Optional RGB tuple for box color
        """
        if not self.enabled:
            return
        
        # Remove old hitbox if exists
        if self._hitbox:
            destroy(self._hitbox)
        
        # Create wireframe cube
        box_color = color.rgb(*debug_color) if debug_color else color.cyan
        
        self._hitbox = Entity(
            model='wireframe_cube',
            position=entity.position,
            scale=(width, height, depth),
            color=box_color,
            alpha=0.6,
            unlit=True
        )
    
    def update(
        self,
        player,
        ground_hit: Optional[Vec3] = None,
        ground_ray_origin: Optional[Vec3] = None,
        ground_ray_distance: float = 5.0,
        hitbox_size: Optional[tuple] = None
    ):
        """Update debug visualization for current frame.
        
        Args:
            player: Player entity
            ground_hit: World position where ground raycast hit (None if no hit)
            ground_ray_origin: Origin of the ground raycast
            ground_ray_distance: Distance of the ground raycast
            hitbox_size: Optional (width, height, depth) tuple for hitbox
        """
        if not self.enabled:
            return
        
        # Clear previous frame's debug entities
        self.clear()
        
        # Draw ground raycast
        if ground_ray_origin:
            self.draw_raycast(
                origin=ground_ray_origin,
                direction=Vec3(0, -1, 0),
                distance=ground_ray_distance,
                hit=ground_hit is not None,
                debug_color=(0, 1, 0) if ground_hit else (1, 0, 0)
            )
        
        # Draw hit point if ground was hit
        if ground_hit:
            self.draw_hit_point(ground_hit)
        
        # Draw player hitbox
        if hitbox_size:
            width, height, depth = hitbox_size
            self.draw_hitbox(player, width, height, depth)
