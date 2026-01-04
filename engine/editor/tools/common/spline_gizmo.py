"""
SplineGizmo: Visual control point handles for spine manipulation.

Renders draggable spheres and curve visualization for spline editing.
"""

from typing import Optional, Callable, List
from panda3d.core import (
    NodePath, GeomNode, Geom, GeomVertexFormat, GeomVertexData,
    GeomVertexWriter, GeomLines, GeomTriangles, LVector3f, Point2,
    CollisionNode, CollisionSphere, CollisionRay, CollisionTraverser,
    CollisionHandlerQueue
)
import math

from engine.editor.tools.common.spline_controller import SplineController
from engine.core.logger import get_logger

logger = get_logger(__name__)


class SplineGizmo:
    """Visual gizmo for manipulating spline control points.
    
    Renders:
    - Control point spheres (draggable)
    - Spline curve visualization (smooth line)
    
    Interaction:
    - Click to select control point
    - Drag to move control point
    - Release to apply changes
    """
    
    # Visual constants
    CONTROL_POINT_RADIUS = 0.08
    CURVE_SAMPLE_POINTS = 30
    
    # Colors
    COLOR_CONTROL_POINT = (1.0, 0.9, 0.2, 1.0)  # Yellow
    COLOR_CONTROL_ACTIVE = (1.0, 0.5, 0.1, 1.0)  # Orange
    COLOR_CURVE = (0.2, 0.8, 0.9, 0.8)          # Cyan
    
    def __init__(self, parent_node: NodePath, controller: SplineController):
        """Initialize spline gizmo.
        
        Args:
            parent_node: Parent node for rendering
            controller: Spline controller to manipulate
        """
        self.parent_node = parent_node
        self.controller = controller
        
        # Rendering
        self.gizmo_root = parent_node.attachNewNode("spline_gizmo")
        self.control_point_nodes: List[NodePath] = []
        self.curve_node: Optional[NodePath] = None
        
        # Interaction
        self.active_point_index: Optional[int] = None
        self.on_changed: Optional[Callable[[], None]] = None
        
        # Collision detection
        self.collision_nodes: List[NodePath] = []
        
        self.gizmo_root.hide()  # Hidden by default
        
    def show(self):
        """Show the gizmo and update visualization."""
        self._build_visualization()
        self.gizmo_root.show()
        
    def hide(self):
        """Hide the gizmo."""
        self.gizmo_root.hide()
        
    def update(self):
        """Update visualization from current spline state."""
        if self.gizmo_root.is_hidden():
            return
        self._build_visualization()
        
    def _build_visualization(self):
        """Build/rebuild the visual representation."""
        # Clear existing
       
        for node in self.control_point_nodes:
            node.removeNode()
        self.control_point_nodes.clear()
        
        for node in self.collision_nodes:
            node.removeNode()
        self.collision_nodes.clear()
        
        if self.curve_node:
            self.curve_node.removeNode()
            self.curve_node = None
            
        # Get control points from controller
        control_points = self.controller.get_control_points()
        if len(control_points) < 4:
            return
            
        # Build control point spheres
        for i, pos in enumerate(control_points):
            # Skip p0 and p3 (tangent points) - only show p1 and p2
            if i == 0 or i == 3:
                continue
                
            sphere_node = self._create_sphere(pos, self.CONTROL_POINT_RADIUS)
            sphere_node.reparentTo(self.gizmo_root)
            
            # Color
            is_active = (i == self.active_point_index)
            color = self.COLOR_CONTROL_ACTIVE if is_active else self.COLOR_CONTROL_POINT
            sphere_node.setColor(*color)
            
            self.control_point_nodes.append(sphere_node)
            
            # Collision sphere for picking
            col_node = self._create_collision_sphere(pos, self.CONTROL_POINT_RADIUS * 1.2, f"cp_{i}")
            col_node.reparentTo(self.gizmo_root)
            self.collision_nodes.append(col_node)
            
        # Build curve visualization
        if self.controller.spline:
            curve_samples = self.controller.spline.sample_points(self.CURVE_SAMPLE_POINTS)
            self.curve_node = self._create_curve_line(curve_samples)
            self.curve_node.reparentTo(self.gizmo_root)
            self.curve_node.setColor(*self.COLOR_CURVE)
            
    def _create_sphere(self, center: LVector3f, radius: float) -> NodePath:
        """Create a sphere geometry.
        
        Args:
            center: Sphere center
            radius: Sphere radius
            
        Returns:
            NodePath with sphere geometry
        """
        # Simple ico-sphere (low-poly for performance)
        vdata = GeomVertexData('sphere', GeomVertexFormat.getV3n3(), Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        
        # Simplified sphere: 3 rings + top/bottom
        rings = 3
        segments = 8
        
        # Top vertex
        vertex.addData3(center.x, center.y, center.z + radius)
        normal.addData3(0, 0, 1)
        
        # Ring vertices
        for ring in range(1, rings):
            phi = (math.pi * ring) / rings
            for seg in range(segments):
                theta = (2 * math.pi * seg) / segments
                x = radius * math.sin(phi) * math.cos(theta)
                y = radius * math.sin(phi) * math.sin(theta)
                z = radius * math.cos(phi)
                
                vertex.addData3(center.x + x, center.y + y, center.z + z)
                # Normal is same as position for sphere
                normal.addData3(x/radius, y/radius, z/radius)
                
        # Bottom vertex
        vertex.addData3(center.x, center.y, center.z - radius)
        normal.addData3(0, 0, -1)
        
        # Build triangles
        prim = GeomTriangles(Geom.UHStatic)
        
        # Top cap
        for seg in range(segments):
            next_seg = (seg + 1) % segments
            prim.addVertices(0, seg + 1, next_seg + 1)
            
        # Middle rings
        for ring in range(rings - 2):
            base = 1 + ring * segments
            next_base = 1 + (ring + 1) * segments
            for seg in range(segments):
                next_seg = (seg + 1) % segments
                
                # Two triangles per quad
                prim.addVertices(base + seg, next_base + seg, base + next_seg)
                prim.addVertices(base + next_seg, next_base + seg, next_base + next_seg)
                
        # Bottom cap
        bottom_idx = 1 + (rings - 1) * segments
        base = bottom_idx - segments
        for seg in range(segments):
            next_seg = (seg + 1) % segments
            prim.addVertices(bottom_idx, base + next_seg, base + seg)
            
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        
        node = GeomNode('sphere')
        node.addGeom(geom)
        
        return NodePath(node)
    
    def _create_curve_line(self, points: List[LVector3f]) -> NodePath:
        """Create a line strip for the curve.
        
        Args:
            points: Sampled points along the curve
            
        Returns:
            NodePath with line geometry
        """
        vdata = GeomVertexData('curve', GeomVertexFormat.getV3(), Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        
        for p in points:
            vertex.addData3(p.x, p.y, p.z)
            
        prim = GeomLines(Geom.UHStatic)
        for i in range(len(points) - 1):
            prim.addVertices(i, i + 1)
            
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        
        node = GeomNode('curve')
        node.addGeom(geom)
        
        return NodePath(node)
    
    def _create_collision_sphere(self, center: LVector3f, radius: float, name: str) -> NodePath:
        """Create a collision sphere for picking.
        
        Args:
            center: Sphere center
            radius: Sphere radius
            name: Collision node name
            
        Returns:
            NodePath with collision node
        """
        col_sphere = CollisionSphere(center, radius)
        col_node = CollisionNode(name)
        col_node.addSolid(col_sphere)
        col_node.setFromCollideMask(0)  # Don't collide with anything
        col_node.setIntoCollideMask(1)  # Can be collided into
        
        return NodePath(col_node)
    
    def pick_control_point(self, camera: NodePath, mouse_pos: Point2) -> Optional[int]:
        """Pick a control point via raycast.
        
        Args:
            camera: Camera node
            mouse_pos: Normalized mouse position
            
        Returns:
            Control point index (1 or 2), or None
        """
        # Create ray from camera through mouse
        # Note: This is simplified. In practice, use camera.getRelativePoint() properly
        # For now, return None (will be enhanced when integrated)
        return None
    
    def begin_drag(self, point_index: int):
        """Begin dragging a control point.
        
        Args:
            point_index: Index of control point to drag
        """
        self.active_point_index = point_index
        self.update()
        logger.debug(f"Begin dragging control point {point_index}")
        
    def update_drag(self, new_position: LVector3f):
        """Update control point position during drag.
        
        Args:
            new_position: New world position
        """
        if self.active_point_index is None:
            return
            
        self.controller.move_control_point(self.active_point_index, new_position)
        self.update()
        
    def end_drag(self):
        """End control point drag."""
        if self.active_point_index is not None:
            logger.debug(f"End dragging control point {self.active_point_index}")
            self.active_point_index = None
            self.update()
            
            # Notify change
            if self.on_changed:
                self.on_changed()
                
    def cleanup(self):
        """Clean up resources."""
        if self.gizmo_root:
            self.gizmo_root.removeNode()
