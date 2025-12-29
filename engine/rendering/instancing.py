"""Hardware instancing for repetitive world decorations."""

from panda3d.core import (
    NodePath, GeomNode, Geom, GeomVertexData, GeomVertexFormat,
    GeomVertexWriter, GeomTriangles, LVector3f, Texture,
    GeomEnums, Shader
)

class InstancedManager:
    """Manages hardware instancing for decorations like grass and rocks."""
    
    def __init__(self, base):
        self.base = base
        self.prototypes = {} # mesh_name -> NodePath
        
    def create_prototype(self, name, mesh_node):
        """Register a base mesh to be instanced."""
        placeholder = self.base.render.attachNewNode(f"proto_{name}")
        placeholder.attachNewNode(mesh_node)
        placeholder.hide()
        self.prototypes[name] = placeholder
        
    def spawn_instances(self, name, positions, parent=None):
        """Spawn multiple instances using hardware instancing.
        
        This implementation uses NodePath.instanceTo as a base,
        but for true HW instancing we would use setInstanceCount.
        
        For initial Phase 6, we'll use Panda3D's built-in instancing
        which is highly efficient for identical objects.
        """
        if name not in self.prototypes:
            return None
            
        root = (parent or self.base.render).attachNewNode(f"instanced_{name}")
        proto = self.prototypes[name]
        
        for pos in positions:
            instance = proto.instanceTo(root)
            instance.setPos(pos)
            # Add some random rotation for variety
            instance.setH(hash(pos) % 360)
            
        return root
