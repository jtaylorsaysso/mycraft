"""Debug visualization for collision system.

Provides visual feedback for raycasts, hitboxes, and collision points
to help debug and tune collision behavior during playtesting.
"""

from typing import Optional, List
from panda3d.core import LVector3f as Vec3, NodePath, LineSegs, LVector4f


class CollisionDebugRenderer:
    """Renders visual debug information for collision system using Panda3D."""
    
    def __init__(self, render_node: NodePath):
        """Initialize debug renderer.
        
        Args:
            render_node: Panda3D render NodePath to attach debug visuals to
        """
        self.enabled = False
        self.render = render_node
        self._debug_root = None
        self._line_nodes: List[NodePath] = []
        
    def toggle(self) -> bool:
        """Toggle debug rendering on/off. Returns new state."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.clear()
        return self.enabled
    
    def clear(self):
        """Remove all debug visualization entities."""
        if self._debug_root:
            self._debug_root.removeNode()
            self._debug_root = None
        self._line_nodes = []
    
    def _ensure_root(self):
        """Ensure debug root node exists."""
        if not self._debug_root:
            self._debug_root = self.render.attachNewNode("collision_debug")
    
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
        
        self._ensure_root()
        
        # Calculate endpoint
        end = origin + direction * distance
        
        # Choose color based on hit status
        if debug_color:
            line_color = LVector4f(*debug_color, 1.0)
        else:
            line_color = LVector4f(0, 1, 0, 1) if hit else LVector4f(1, 0, 0, 1)
        
        # Create line using LineSegs
        lines = LineSegs()
        lines.setThickness(2.0)
        lines.setColor(line_color)
        lines.moveTo(origin)
        lines.drawTo(end)
        
        # Create node and attach to debug root
        line_node = self._debug_root.attachNewNode(lines.create())
        self._line_nodes.append(line_node)
    
    def draw_hit_point(self, position: Vec3, normal: Optional[Vec3] = None):
        """Draw a visual indicator at a raycast hit point.
        
        Args:
            position: World position where the ray hit
            normal: Optional surface normal at hit point
        """
        if not self.enabled:
            return
        
        self._ensure_root()
        
        # Create a small cross at the hit point
        lines = LineSegs()
        lines.setThickness(3.0)
        lines.setColor(LVector4f(1, 1, 0, 1))  # Yellow
        
        # Draw cross
        size = 0.2
        lines.moveTo(position + Vec3(size, 0, 0))
        lines.drawTo(position + Vec3(-size, 0, 0))
        lines.moveTo(position + Vec3(0, size, 0))
        lines.drawTo(position + Vec3(0, -size, 0))
        lines.moveTo(position + Vec3(0, 0, size))
        lines.drawTo(position + Vec3(0, 0, -size))
        
        # Draw normal if provided
        if normal:
            lines.setColor(LVector4f(0, 1, 1, 1))  # Cyan
            lines.moveTo(position)
            lines.drawTo(position + normal * 0.5)
        
        line_node = self._debug_root.attachNewNode(lines.create())
        self._line_nodes.append(line_node)
    
    def draw_hitbox(
        self,
        position: Vec3,
        width: float,
        height: float,
        depth: float,
        debug_color: Optional[tuple] = None
    ):
        """Draw a wireframe box showing collision bounds.
        
        Args:
            position: Center position of the hitbox
            width: Width of the hitbox (X axis)
            height: Height of the hitbox (Z axis in Panda3D)
            depth: Depth of the hitbox (Y axis in Panda3D)
            debug_color: Optional RGB tuple for box color
        """
        if not self.enabled:
            return
        
        self._ensure_root()
        
        # Create wireframe cube
        box_color = LVector4f(*debug_color, 1.0) if debug_color else LVector4f(0, 1, 1, 1)
        
        lines = LineSegs()
        lines.setThickness(2.0)
        lines.setColor(box_color)
        
        # Calculate corners
        hw, hh, hd = width/2, height/2, depth/2
        corners = [
            Vec3(-hw, -hd, -hh), Vec3(hw, -hd, -hh),
            Vec3(hw, hd, -hh), Vec3(-hw, hd, -hh),
            Vec3(-hw, -hd, hh), Vec3(hw, -hd, hh),
            Vec3(hw, hd, hh), Vec3(-hw, hd, hh),
        ]
        
        # Offset by position
        corners = [c + position for c in corners]
        
        # Draw bottom face
        for i in range(4):
            lines.moveTo(corners[i])
            lines.drawTo(corners[(i+1) % 4])
        
        # Draw top face
        for i in range(4, 8):
            lines.moveTo(corners[i])
            lines.drawTo(corners[4 + ((i+1) % 4)])
        
        # Draw vertical edges
        for i in range(4):
            lines.moveTo(corners[i])
            lines.drawTo(corners[i+4])
        
        line_node = self._debug_root.attachNewNode(lines.create())
        self._line_nodes.append(line_node)
    
    def update(
        self,
        player_position: Vec3,
        ground_hit: Optional[Vec3] = None,
        ground_ray_origin: Optional[Vec3] = None,
        ground_ray_distance: float = 5.0,
        hitbox_size: Optional[tuple] = None
    ):
        """Update debug visualization for current frame.
        
        Args:
            player_position: Player entity position
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
                direction=Vec3(0, 0, -1),
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
            self.draw_hitbox(player_position, width, height, depth)
