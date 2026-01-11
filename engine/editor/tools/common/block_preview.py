"""
Visual preview utilities for the POI editor.

Provides:
1. Ghost block preview showing where a block will be placed
2. Selection highlight for hovered blocks
"""

from typing import Optional, Tuple
from panda3d.core import (
    NodePath, GeomNode, GeomVertexFormat, GeomVertexData,
    GeomVertexWriter, GeomTriangles, Geom, Vec4, TransparencyAttrib
)


class BlockPreview:
    """
    Semi-transparent ghost block showing placement preview.
    """
    
    def __init__(self, parent: NodePath):
        """
        Initialize the block preview.
        
        Args:
            parent: Parent NodePath to attach to
        """
        self.root = parent.attachNewNode("block_preview")
        self._mesh_node: Optional[NodePath] = None
        self._current_pos: Optional[Tuple[int, int, int]] = None
        self._color = (0.5, 0.7, 1.0, 0.4)  # Light blue, semi-transparent
        
        self._build_mesh()
        self.hide()
        
    def _build_mesh(self):
        """Build the ghost block mesh."""
        if self._mesh_node:
            self._mesh_node.removeNode()
            
        # Setup Vertex Data
        fmt = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData('preview_data', fmt, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        color = GeomVertexWriter(vdata, 'color')
        
        tris = GeomTriangles(Geom.UHStatic)
        v_idx = 0
        
        r, g, b, a = self._color
        
        # Corners of unit cube centered at origin
        corners = [
            (-0.5, -0.5, -0.5),  # 0
            (0.5, -0.5, -0.5),   # 1
            (0.5, 0.5, -0.5),    # 2
            (-0.5, 0.5, -0.5),   # 3
            (-0.5, -0.5, 0.5),   # 4
            (0.5, -0.5, 0.5),    # 5
            (0.5, 0.5, 0.5),     # 6
            (-0.5, 0.5, 0.5),    # 7
        ]
        
        # Face definitions (6 faces, 4 vertices each)
        faces = [
            [0, 1, 5, 4],  # Front (Y-)
            [2, 3, 7, 6],  # Back (Y+)
            [3, 0, 4, 7],  # Left (X-)
            [1, 2, 6, 5],  # Right (X+)
            [3, 2, 1, 0],  # Bottom (Z-)
            [4, 5, 6, 7],  # Top (Z+)
        ]
        
        for face in faces:
            for c_idx in face:
                cx, cy, cz = corners[c_idx]
                vertex.addData3(cx, cy, cz)
                color.addData4(r, g, b, a)
            
            tris.addVertices(v_idx, v_idx + 1, v_idx + 2)
            tris.addVertices(v_idx, v_idx + 2, v_idx + 3)
            v_idx += 4
            
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode('preview_geom')
        node.addGeom(geom)
        
        self._mesh_node = self.root.attachNewNode(node)
        self._mesh_node.setTransparency(TransparencyAttrib.MAlpha)
        # Render above normal geometry
        self._mesh_node.setBin("transparent", 10)
        
    def set_color(self, color: Tuple[float, float, float, float]):
        """Set the preview color."""
        self._color = color
        self._build_mesh()
        
    def show_at(self, pos: Tuple[int, int, int]):
        """Show the preview at the given grid position."""
        self._current_pos = pos
        self.root.setPos(pos[0], pos[1], pos[2])
        self.root.show()
        
    def hide(self):
        """Hide the preview."""
        self._current_pos = None
        self.root.hide()
        
    @property
    def position(self) -> Optional[Tuple[int, int, int]]:
        """Get the current preview position."""
        return self._current_pos
        
    def cleanup(self):
        """Remove the preview from the scene."""
        self.root.removeNode()


class SelectionHighlight:
    """
    Wireframe highlight around a selected/hovered block.
    """
    
    def __init__(self, parent: NodePath):
        """
        Initialize the selection highlight.
        
        Args:
            parent: Parent NodePath to attach to
        """
        self.root = parent.attachNewNode("selection_highlight")
        self._build_wireframe()
        self.hide()
        
    def _build_wireframe(self):
        """Build wireframe cube using line segments."""
        from panda3d.core import LineSegs
        
        lines = LineSegs()
        lines.setColor(1, 1, 0, 1)  # Yellow
        lines.setThickness(2)
        
        # Slightly larger than 1x1x1 to avoid z-fighting
        s = 0.51
        
        # 12 edges of a cube
        # Bottom face
        lines.moveTo(-s, -s, -s)
        lines.drawTo(s, -s, -s)
        lines.drawTo(s, s, -s)
        lines.drawTo(-s, s, -s)
        lines.drawTo(-s, -s, -s)
        
        # Top face
        lines.moveTo(-s, -s, s)
        lines.drawTo(s, -s, s)
        lines.drawTo(s, s, s)
        lines.drawTo(-s, s, s)
        lines.drawTo(-s, -s, s)
        
        # Vertical edges
        lines.moveTo(-s, -s, -s)
        lines.drawTo(-s, -s, s)
        
        lines.moveTo(s, -s, -s)
        lines.drawTo(s, -s, s)
        
        lines.moveTo(s, s, -s)
        lines.drawTo(s, s, s)
        
        lines.moveTo(-s, s, -s)
        lines.drawTo(-s, s, s)
        
        node = lines.create()
        self.root.attachNewNode(node)
        
    def show_at(self, pos: Tuple[int, int, int]):
        """Show highlight at the given grid position."""
        self.root.setPos(pos[0], pos[1], pos[2])
        self.root.show()
        
    def hide(self):
        """Hide the highlight."""
        self.root.hide()
        
    def cleanup(self):
        """Remove from scene."""
        self.root.removeNode()
