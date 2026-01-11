"""
Voxel picking utility for the POI editor.

Provides accurate raycasting against voxel blocks to determine:
1. Which block was clicked
2. Which face of the block was clicked
3. The position for placing an adjacent block
"""

from typing import Optional, Tuple, Dict
from panda3d.core import (
    NodePath, CollisionTraverser, CollisionHandlerQueue,
    CollisionNode, CollisionRay, CollisionBox, BitMask32,
    Point3, Vec3
)


# Face normal vectors (used to determine placement position)
FACE_NORMALS = {
    'top': Vec3(0, 0, 1),
    'bottom': Vec3(0, 0, -1),
    'north': Vec3(0, 1, 0),
    'south': Vec3(0, -1, 0),
    'east': Vec3(1, 0, 0),
    'west': Vec3(-1, 0, 0),
}


class VoxelPickResult:
    """Result of a voxel pick operation."""
    
    def __init__(
        self,
        hit_pos: Tuple[int, int, int],
        face: str,
        world_point: Point3,
        normal: Vec3
    ):
        self.hit_pos = hit_pos  # Grid position of the hit block
        self.face = face  # Which face was hit ('top', 'bottom', etc.)
        self.world_point = world_point  # Exact world hit point
        self.normal = normal  # Face normal
        
    @property
    def adjacent_pos(self) -> Tuple[int, int, int]:
        """Grid position adjacent to the hit face (where a new block would go)."""
        x, y, z = self.hit_pos
        return (
            x + int(self.normal.x),
            y + int(self.normal.y),
            z + int(self.normal.z)
        )


class VoxelPicker:
    """
    Handles mouse-to-voxel raycasting for the editor.
    
    Creates collision boxes for each voxel and uses Panda3D's collision
    system for accurate picking, including face detection.
    """
    
    # Collision mask for voxel picking
    PICK_MASK = BitMask32.bit(5)
    
    def __init__(self, base):
        """
        Initialize the voxel picker.
        
        Args:
            base: Panda3D ShowBase instance
        """
        self.base = base
        
        # Collision system
        self.traverser = CollisionTraverser('voxel_picker')
        self.handler = CollisionHandlerQueue()
        
        # Ray setup
        self.ray = CollisionRay()
        self.ray_node = CollisionNode('voxel_pick_ray')
        self.ray_node.addSolid(self.ray)
        self.ray_node.setFromCollideMask(self.PICK_MASK)
        self.ray_node.setIntoCollideMask(BitMask32.allOff())
        self.ray_np = base.camera.attachNewNode(self.ray_node)
        self.traverser.addCollider(self.ray_np, self.handler)
        
        # Root for collision geometry (separate from visual mesh)
        self.collision_root = NodePath('voxel_collision_root')
        
        # Track collision nodes per voxel position
        self._collision_nodes: Dict[Tuple[int, int, int], NodePath] = {}
        
    def set_parent(self, parent: NodePath):
        """Attach collision root to a parent node."""
        self.collision_root.reparentTo(parent)
        
    def add_voxel(self, pos: Tuple[int, int, int]):
        """Add a pickable collision box at the given grid position."""
        if pos in self._collision_nodes:
            return  # Already exists
            
        x, y, z = pos
        
        # Create collision node
        cnode = CollisionNode(f'voxel_{x}_{y}_{z}')
        # Box centered at origin with half-extents of 0.5
        box = CollisionBox(Point3(0, 0, 0), 0.5, 0.5, 0.5)
        cnode.addSolid(box)
        cnode.setIntoCollideMask(self.PICK_MASK)
        cnode.setFromCollideMask(BitMask32.allOff())
        
        # Create NodePath and position it
        np = self.collision_root.attachNewNode(cnode)
        np.setPos(x, y, z)
        
        # Store reference
        self._collision_nodes[pos] = np
        
    def remove_voxel(self, pos: Tuple[int, int, int]):
        """Remove the collision box at the given position."""
        if pos in self._collision_nodes:
            self._collision_nodes[pos].removeNode()
            del self._collision_nodes[pos]
            
    def clear(self):
        """Remove all collision boxes."""
        for np in self._collision_nodes.values():
            np.removeNode()
        self._collision_nodes.clear()
        
    def sync_with_canvas(self, voxels: Dict):
        """
        Sync collision boxes with a VoxelCanvas's voxel dictionary.
        
        Args:
            voxels: Dictionary of {(x,y,z): color} from VoxelCanvas
        """
        # Add missing voxels
        for pos in voxels:
            if pos not in self._collision_nodes:
                self.add_voxel(pos)
                
        # Remove extra voxels
        to_remove = [pos for pos in self._collision_nodes if pos not in voxels]
        for pos in to_remove:
            self.remove_voxel(pos)
            
    def pick(self) -> Optional[VoxelPickResult]:
        """
        Perform a pick at the current mouse position.
        
        Returns:
            VoxelPickResult if a voxel was hit, None otherwise.
        """
        if not self.base.mouseWatcherNode.hasMouse():
            return None
            
        # Update ray from mouse
        mpos = self.base.mouseWatcherNode.getMouse()
        self.ray.setFromLens(self.base.camNode, mpos.x, mpos.y)
        
        # Traverse
        self.traverser.traverse(self.collision_root)
        
        if self.handler.getNumEntries() == 0:
            return None
            
        # Sort by distance and get closest
        self.handler.sortEntries()
        entry = self.handler.getEntry(0)
        
        # Get hit info
        hit_np = entry.getIntoNodePath()
        surface_point = entry.getSurfacePoint(self.collision_root)
        surface_normal = entry.getSurfaceNormal(self.collision_root)
        
        # Parse position from node name
        name = hit_np.getName()
        try:
            parts = name.split('_')
            x, y, z = int(parts[1]), int(parts[2]), int(parts[3])
        except (IndexError, ValueError):
            return None
            
        # Determine which face based on normal
        face = self._normal_to_face(surface_normal)
        
        return VoxelPickResult(
            hit_pos=(x, y, z),
            face=face,
            world_point=surface_point,
            normal=FACE_NORMALS.get(face, Vec3(0, 0, 1))
        )
        
    def _normal_to_face(self, normal: Vec3) -> str:
        """Convert a surface normal to a face name."""
        # Find closest matching face
        best_face = 'top'
        best_dot = -999
        
        for face, face_normal in FACE_NORMALS.items():
            dot = normal.dot(face_normal)
            if dot > best_dot:
                best_dot = dot
                best_face = face
                
        return best_face
        
    def cleanup(self):
        """Clean up collision system."""
        self.clear()
        self.ray_np.removeNode()
        self.collision_root.removeNode()
