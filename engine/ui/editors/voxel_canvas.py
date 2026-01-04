from panda3d.core import NodePath, GeomNode, GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles, Geom, Vec3, Vec4, LineSegs

class VoxelCanvas:
    """
    Manages the 3D data and rendering for the Voxel Model Editor.
    """
    def __init__(self, base):
        self.base = base
        # Root node for the editor scene
        self.root = NodePath("VoxelEditorRoot")
        self.voxel_node = self.root.attachNewNode("VoxelMesh")
        self.grid_node = self.root.attachNewNode("Grid")
        
        # Voxel Data: {(x, y, z): (r, g, b, a)}
        self.voxels = {}
        
        # Setup visualization
        self._build_grid()
        self.rebuild_mesh()
        
    def _build_grid(self):
        """Draws a reference grid on the XZ plane."""
        lines = LineSegs()
        lines.setColor(0.3, 0.3, 0.3, 1)
        
        # Grid size
        size = 10
        step = 1
        
        for i in range(-size, size + 1):
            # X lines
            lines.moveTo(i, -size, 0)
            lines.drawTo(i, size, 0)
            # Y lines
            lines.moveTo(-size, i, 0)
            lines.drawTo(size, i, 0)
            
        # Axes
        lines.setColor(1, 0, 0, 1) # X
        lines.moveTo(0, 0, 0)
        lines.drawTo(2, 0, 0)
        
        lines.setColor(0, 1, 0, 1) # Y
        lines.moveTo(0, 0, 0)
        lines.drawTo(0, 2, 0)
        
        lines.setColor(0, 0, 1, 1) # Z
        lines.moveTo(0, 0, 0)
        lines.drawTo(0, 0, 2)
            
        node = lines.create()
        self.grid_node.attachNewNode(node)
        
    def add_voxel(self, pos, color=(1, 1, 1, 1)):
        """Adds or updates a voxel at the given (x, y, z) tuple."""
        # Round position to nearest int
        grid_pos = (round(pos[0]), round(pos[1]), round(pos[2]))
        self.voxels[grid_pos] = color
        self.rebuild_mesh()
        
    def remove_voxel(self, pos):
        """Removes a voxel at the given position."""
        grid_pos = (round(pos[0]), round(pos[1]), round(pos[2]))
        if grid_pos in self.voxels:
            del self.voxels[grid_pos]
            self.rebuild_mesh()
            
    def clear(self):
        """Clears all voxels."""
        self.voxels = {}
        self.rebuild_mesh()

    def rebuild_mesh(self):
        """Rebuilds the GeomNode from current voxel data."""
        self.voxel_node.removeNode()
        self.voxel_node = self.root.attachNewNode("VoxelMesh")
        
        if not self.voxels:
            return

        # Setup Vertex Data
        format = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData('voxel_data', format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        color = GeomVertexWriter(vdata, 'color')
        
        tris = GeomTriangles(Geom.UHStatic)
        v_idx = 0
        
        # Simple cube generation (non-optimized / no culling for now)
        # TODO: Optimize by checking neighbors
        for pos, col in self.voxels.items():
            x, y, z = pos
            r, g, b, a = col
            
            # 8 corners of a cube 
            # We'll just generate 6 faces manually for simplicity in this pass
            # Or simpler: Reference a unit cube geometry? 
            # Let's write raw vertices for a clean start.
            
            # Offsets for faces
            offsets = [
                (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), # Bottom
                (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)  # Top
            ]
            
            # Scale slightly down to see edges? No, tight voxels.
            scale = 0.5 # Centered?
            # Let's assume input pos is center. 
            # -0.5 to +0.5
            
            # Face definitions (Clockwise winding)
            faces = [
                # Front (Y-)
                [0, 1, 5, 4],
                # Back (Y+)
                [2, 3, 7, 6],
                # Left (X-)
                [3, 0, 4, 7],
                # Right (X+)
                [1, 2, 6, 5],
                # Bottom (Z-)
                [3, 2, 1, 0],
                # Top (Z+)
                [4, 5, 6, 7]
            ]
            
            # Define corners relative to center (x,y,z)
            corners = [
                (x - 0.5, y - 0.5, z - 0.5), # 0: - - -
                (x + 0.5, y - 0.5, z - 0.5), # 1: + - -
                (x + 0.5, y + 0.5, z - 0.5), # 2: + + -
                (x - 0.5, y + 0.5, z - 0.5), # 3: - + -
                (x - 0.5, y - 0.5, z + 0.5), # 4: - - +
                (x + 0.5, y - 0.5, z + 0.5), # 5: + - +
                (x + 0.5, y + 0.5, z + 0.5), # 6: + + +
                (x - 0.5, y + 0.5, z + 0.5), # 7: - + +
            ]

            for face in faces:
                # Add 4 vertices for the face
                for c_idx in face:
                    cx, cy, cz = corners[c_idx]
                    vertex.addData3(cx, cy, cz)
                    color.addData4(r, g, b, a)
                
                # Add 2 triangles
                tris.addVertices(v_idx, v_idx + 1, v_idx + 2)
                tris.addVertices(v_idx, v_idx + 2, v_idx + 3)
                v_idx += 4
                
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode('gnode')
        node.addGeom(geom)
        self.voxel_node.attachNewNode(node)
        
    def cleanup(self):
        """Destroys the rendering nodes."""
        self.root.removeNode()
