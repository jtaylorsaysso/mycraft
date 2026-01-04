"""
TransformGizmo: Visual 3D manipulation handles for bones.

Provides XYZ arrows for translation, rotation rings, and scale handles.
"""

from typing import Optional, Tuple
from panda3d.core import (
    NodePath, LineSegs, LVector3f, LVector4f, GeomNode,
    CollisionNode, CollisionSphere, CollisionRay, BitMask32
)
from engine.core.logger import get_logger

logger = get_logger(__name__)


class TransformGizmo:
    """Visual manipulation handles for translate/rotate/scale operations.
    
    Features:
    - XYZ arrows for translation (red/green/blue)
    - Rotation rings around each axis
    - Uniform scale handle at center
    - Collision detection for handle picking
    """
    
    # Gizmo display modes
    MODE_TRANSLATE = "translate"
    MODE_ROTATE = "rotate"
    MODE_SCALE = "scale"
    
    # Collision masks
    GIZMO_MASK = BitMask32.bit(2)
    
    # Visual constants
    ARROW_LENGTH = 0.4
    ARROW_THICKNESS = 2
    RING_RADIUS = 0.3
    RING_SEGMENTS = 32
    HANDLE_SIZE = 0.08
    
    def __init__(self, parent_node: NodePath):
        """Initialize transform gizmo.
        
        Args:
            parent_node: Parent node to attach gizmo to
        """
        self.parent_node = parent_node
        self.root = parent_node.attachNewNode("TransformGizmo")
        
        # Current state
        self.mode = self.MODE_TRANSLATE
        self.visible = False
        self.target_bone: Optional[NodePath] = None
        
        # Gizmo components
        self.translate_gizmo: Optional[NodePath] = None
        self.rotate_gizmo: Optional[NodePath] = None
        self.scale_gizmo: Optional[NodePath] = None
        
        # Collision nodes for picking
        self.handle_colliders = {}  # axis -> NodePath
        
        # Build all gizmo modes
        self._build_translate_gizmo()
        self._build_rotate_gizmo()
        self._build_scale_gizmo()
        
        # Start hidden
        self.root.hide()
        
    def set_mode(self, mode: str):
        """Set gizmo display mode.
        
        Args:
            mode: One of MODE_TRANSLATE, MODE_ROTATE, MODE_SCALE
        """
        self.mode = mode
        self._update_visibility()
    
    def set_visible(self, visible: bool):
        """Show or hide the gizmo.
        
        Args:
            visible: Whether gizmo should be visible
        """
        if visible:
            if self.target_bone:
                self.root.show()
                self.visible = True
        else:
            self.root.hide()
            self.visible = False
        
        
    def attach_to(self, bone_node: NodePath):
        """Position gizmo at a bone.
        
        Args:
            bone_node: NodePath of bone to attach to
        """
        self.target_bone = bone_node
        if bone_node:
            # Position gizmo at bone's world position
            world_pos = bone_node.getPos(self.parent_node)
            self.root.setPos(world_pos)
            self.root.show()
            self.visible = True
        else:
            self.root.hide()
            self.visible = False
            
    def detach(self):
        """Hide and detach gizmo."""
        self.target_bone = None
        self.root.hide()
        self.visible = False
        
    def get_active_axis(self, collision_entry) -> Optional[str]:
        """Get which axis handle was picked.
        
        Args:
            collision_entry: Collision entry from picker
            
        Returns:
            Axis name ('x', 'y', 'z', 'uniform') or None
        """
        into_node = collision_entry.getIntoNodePath()
        axis = into_node.getTag("gizmo_axis")
        return axis if axis else None
        
    def _update_visibility(self):
        """Update which gizmo components are visible."""
        if self.translate_gizmo:
            self.translate_gizmo.show() if self.mode == self.MODE_TRANSLATE else self.translate_gizmo.hide()
        if self.rotate_gizmo:
            self.rotate_gizmo.show() if self.mode == self.MODE_ROTATE else self.rotate_gizmo.hide()
        if self.scale_gizmo:
            self.scale_gizmo.show() if self.mode == self.MODE_SCALE else self.scale_gizmo.hide()
            
    def _build_translate_gizmo(self):
        """Build XYZ arrow handles for translation."""
        self.translate_gizmo = self.root.attachNewNode("TranslateGizmo")
        
        axes = [
            ('x', LVector4f(1, 0, 0, 1), LVector3f(1, 0, 0)),  # Red X
            ('y', LVector4f(0, 1, 0, 1), LVector3f(0, 1, 0)),  # Green Y
            ('z', LVector4f(0, 0, 1, 1), LVector3f(0, 0, 1)),  # Blue Z
        ]
        
        for axis_name, color, direction in axes:
            # Draw arrow line
            lines = LineSegs()
            lines.setThickness(self.ARROW_THICKNESS)
            lines.setColor(color)
            
            # Arrow shaft
            end_pos = direction * self.ARROW_LENGTH
            lines.moveTo(0, 0, 0)
            lines.drawTo(end_pos)
            
            # Arrow head (simple cone approximation with lines)
            head_base = direction * (self.ARROW_LENGTH * 0.85)
            head_size = 0.05
            
            # Create perpendicular vectors for arrow head
            if axis_name == 'x':
                perp1, perp2 = LVector3f(0, 1, 0), LVector3f(0, 0, 1)
            elif axis_name == 'y':
                perp1, perp2 = LVector3f(1, 0, 0), LVector3f(0, 0, 1)
            else:  # z
                perp1, perp2 = LVector3f(1, 0, 0), LVector3f(0, 1, 0)
                
            # Draw 4 lines from base to tip for arrow head
            for angle in [0, 90, 180, 270]:
                import math
                rad = math.radians(angle)
                offset = (perp1 * math.cos(rad) + perp2 * math.sin(rad)) * head_size
                lines.moveTo(head_base + offset)
                lines.drawTo(end_pos)
                
            arrow_node = lines.create()
            arrow_np = self.translate_gizmo.attachNewNode(arrow_node)
            
            # Add collision sphere at arrow tip for picking
            coll_node = CollisionNode(f"gizmo_translate_{axis_name}")
            coll_node.setFromCollideMask(BitMask32.allOff())
            coll_node.setIntoCollideMask(self.GIZMO_MASK)
            coll_sphere = CollisionSphere(end_pos, self.HANDLE_SIZE)
            coll_node.addSolid(coll_sphere)
            
            coll_np = arrow_np.attachNewNode(coll_node)
            coll_np.setTag("gizmo_axis", axis_name)
            self.handle_colliders[f"translate_{axis_name}"] = coll_np
            
    def _build_rotate_gizmo(self):
        """Build rotation ring handles."""
        self.rotate_gizmo = self.root.attachNewNode("RotateGizmo")
        
        axes = [
            ('x', LVector4f(1, 0, 0, 1), 'yz'),  # Red ring in YZ plane
            ('y', LVector4f(0, 1, 0, 1), 'xz'),  # Green ring in XZ plane
            ('z', LVector4f(0, 0, 1, 1), 'xy'),  # Blue ring in XY plane
        ]
        
        import math
        for axis_name, color, plane in axes:
            lines = LineSegs()
            lines.setThickness(self.ARROW_THICKNESS)
            lines.setColor(color)
            
            # Draw circle in appropriate plane
            for i in range(self.RING_SEGMENTS + 1):
                angle = (i / self.RING_SEGMENTS) * 2 * math.pi
                x = math.cos(angle) * self.RING_RADIUS
                y = math.sin(angle) * self.RING_RADIUS
                
                # Map to correct plane
                if plane == 'xy':
                    pos = LVector3f(x, y, 0)
                elif plane == 'xz':
                    pos = LVector3f(x, 0, y)
                else:  # yz
                    pos = LVector3f(0, x, y)
                    
                if i == 0:
                    lines.moveTo(pos)
                else:
                    lines.drawTo(pos)
                    
            ring_node = lines.create()
            ring_np = self.rotate_gizmo.attachNewNode(ring_node)
            
            # Add collision for picking (simplified - just center sphere)
            coll_node = CollisionNode(f"gizmo_rotate_{axis_name}")
            coll_node.setFromCollideMask(BitMask32.allOff())
            coll_node.setIntoCollideMask(self.GIZMO_MASK)
            coll_sphere = CollisionSphere(0, 0, 0, self.RING_RADIUS)
            coll_node.addSolid(coll_sphere)
            
            coll_np = ring_np.attachNewNode(coll_node)
            coll_np.setTag("gizmo_axis", axis_name)
            self.handle_colliders[f"rotate_{axis_name}"] = coll_np
            
    def _build_scale_gizmo(self):
        """Build uniform scale handle at center."""
        self.scale_gizmo = self.root.attachNewNode("ScaleGizmo")
        
        # Draw small cube at center
        lines = LineSegs()
        lines.setThickness(self.ARROW_THICKNESS)
        lines.setColor(1, 1, 1, 1)  # White
        
        size = self.HANDLE_SIZE
        
        # Draw cube edges
        corners = [
            LVector3f(-size, -size, -size),
            LVector3f(size, -size, -size),
            LVector3f(size, size, -size),
            LVector3f(-size, size, -size),
            LVector3f(-size, -size, size),
            LVector3f(size, -size, size),
            LVector3f(size, size, size),
            LVector3f(-size, size, size),
        ]
        
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom face
            (4, 5), (5, 6), (6, 7), (7, 4),  # Top face
            (0, 4), (1, 5), (2, 6), (3, 7),  # Vertical edges
        ]
        
        for start_idx, end_idx in edges:
            lines.moveTo(corners[start_idx])
            lines.drawTo(corners[end_idx])
            
        cube_node = lines.create()
        cube_np = self.scale_gizmo.attachNewNode(cube_node)
        
        # Collision sphere at center
        coll_node = CollisionNode("gizmo_scale_uniform")
        coll_node.setFromCollideMask(BitMask32.allOff())
        coll_node.setIntoCollideMask(self.GIZMO_MASK)
        coll_sphere = CollisionSphere(0, 0, 0, size * 1.5)
        coll_node.addSolid(coll_sphere)
        
        coll_np = cube_np.attachNewNode(coll_node)
        coll_np.setTag("gizmo_axis", "uniform")
        self.handle_colliders["scale_uniform"] = coll_np
        
    def cleanup(self):
        """Remove gizmo from scene."""
        if self.root:
            self.root.removeNode()
