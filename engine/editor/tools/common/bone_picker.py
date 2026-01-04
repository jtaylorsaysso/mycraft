"""
BonePicker: 3D bone selection via mouse raycasting.

Enables click-to-select bone interaction in the model editor viewport.
"""

from typing import Optional, Dict, Callable
from panda3d.core import (
    NodePath, CollisionTraverser, CollisionNode, CollisionRay,
    CollisionHandlerQueue, CollisionSphere, GeomNode, BitMask32,
    LVector3f, Point2, Point3
)
from engine.animation.skeleton import Skeleton, Bone
from engine.core.logger import get_logger

logger = get_logger(__name__)


class BonePicker:
    """Handles 3D bone selection via mouse raycasting.
    
    Features:
    - Click to select bones in viewport
    - Hover detection for visual feedback
    - Collision spheres at bone joints
    """
    
    # Collision mask for bone picking
    PICK_MASK = BitMask32.bit(1)
    
    def __init__(self, app, parent_node: NodePath):
        """Initialize bone picker.
        
        Args:
            app: EditorApp instance (needs camera, mouse watcher)
            parent_node: Parent node for collision geometry
        """
        self.app = app
        self.parent_node = parent_node
        
        # Collision system
        self.traverser = CollisionTraverser("BonePickerTraverser")
        self.handler = CollisionHandlerQueue()
        
        # Picker ray (attached to camera)
        self.picker_node = CollisionNode("BonePickerRay")
        self.picker_node.setFromCollideMask(self.PICK_MASK)
        self.picker_node.setIntoCollideMask(BitMask32.allOff())
        
        self.picker_ray = CollisionRay()
        self.picker_node.addSolid(self.picker_ray)
        
        self.picker_np = app.camera.attachNewNode(self.picker_node)
        self.traverser.addCollider(self.picker_np, self.handler)
        
        # Bone collision nodes: bone_name -> (NodePath, CollisionNode)
        self.bone_colliders: Dict[str, NodePath] = {}
        
        # Skeleton reference
        self.skeleton: Optional[Skeleton] = None
        self.bone_nodes: Dict[str, NodePath] = {}
        
        # Callbacks
        self.on_bone_selected: Optional[Callable[[str], None]] = None
        self.on_bone_hovered: Optional[Callable[[Optional[str]], None]] = None
        
        # State
        self.enabled = True
        self.hovered_bone: Optional[str] = None
        
    def setup_skeleton(self, skeleton: Skeleton, bone_nodes: Dict[str, NodePath]):
        """Configure picker for a skeleton.
        
        Args:
            skeleton: Skeleton to pick from
            bone_nodes: Dict mapping bone names to NodePaths
        """
        self.skeleton = skeleton
        self.bone_nodes = bone_nodes
        self._rebuild_colliders()
        
    def _rebuild_colliders(self):
        """Create collision spheres for each bone joint."""
        # Clear existing colliders
        for np in self.bone_colliders.values():
            np.removeNode()
        self.bone_colliders.clear()
        
        if not self.skeleton or not self.bone_nodes:
            return
            
        for bone_name, node in self.bone_nodes.items():
            bone = self.skeleton.get_bone(bone_name)
            if not bone:
                continue
                
            # Create collision node
            coll_node = CollisionNode(f"pick_{bone_name}")
            coll_node.setFromCollideMask(BitMask32.allOff())
            coll_node.setIntoCollideMask(self.PICK_MASK)
            
            # Sphere at bone origin (joint position)
            # Size based on bone thickness or default
            radius = self._get_bone_radius(bone_name, bone)
            sphere = CollisionSphere(0, 0, 0, radius)
            coll_node.addSolid(sphere)
            
            # Attach to bone's node so it moves with animation
            coll_np = node.attachNewNode(coll_node)
            coll_np.setTag("bone_name", bone_name)
            self.bone_colliders[bone_name] = coll_np
            
        logger.debug(f"Created {len(self.bone_colliders)} bone colliders")
        
    def _get_bone_radius(self, bone_name: str, bone: Bone) -> float:
        """Get collision radius for a bone.
        
        Args:
            bone_name: Name of the bone
            bone: Bone instance
            
        Returns:
            Collision sphere radius
        """
        # Use thickness map similar to VoxelAvatar
        thickness_map = {
            "hips": 0.25,
            "spine": 0.20,
            "chest": 0.25,
            "head": 0.20,
            "shoulder_left": 0.12, "shoulder_right": 0.12,
            "upper_arm_left": 0.10, "upper_arm_right": 0.10,
            "forearm_left": 0.08, "forearm_right": 0.08,
            "hand_left": 0.06, "hand_right": 0.06,
            "thigh_left": 0.12, "thigh_right": 0.12,
            "shin_left": 0.10, "shin_right": 0.10,
            "foot_left": 0.08, "foot_right": 0.08,
        }
        return thickness_map.get(bone_name, 0.1)
        
    def pick(self, mouse_pos: Point2) -> Optional[str]:
        """Pick a bone under the mouse position.
        
        Args:
            mouse_pos: Normalized mouse position (-1 to 1)
            
        Returns:
            Name of picked bone, or None
        """
        if not self.enabled or not self.skeleton:
            return None
            
        # Set ray from camera through mouse position
        self.picker_ray.setFromLens(
            self.app.camNode,
            mouse_pos.x,
            mouse_pos.y
        )
        
        # Traverse scene for collisions
        self.traverser.traverse(self.parent_node)
        
        if self.handler.getNumEntries() == 0:
            return None
            
        # Sort by distance, pick closest
        self.handler.sortEntries()
        entry = self.handler.getEntry(0)
        
        # Get bone name from collision node tag
        into_node = entry.getIntoNodePath()
        bone_name = into_node.getTag("bone_name")
        
        return bone_name if bone_name else None
        
    def update_hover(self, mouse_pos: Point2):
        """Update hover state based on mouse position.
        
        Args:
            mouse_pos: Normalized mouse position
        """
        if not self.enabled:
            return
            
        bone = self.pick(mouse_pos)
        
        if bone != self.hovered_bone:
            self.hovered_bone = bone
            if self.on_bone_hovered:
                self.on_bone_hovered(bone)
                
    def handle_click(self, mouse_pos: Point2) -> Optional[str]:
        """Handle mouse click to select a bone.
        
        Args:
            mouse_pos: Normalized mouse position
            
        Returns:
            Selected bone name, or None
        """
        if not self.enabled:
            return None
            
        bone = self.pick(mouse_pos)
        
        if bone and self.on_bone_selected:
            self.on_bone_selected(bone)
            
        return bone
        
    def set_enabled(self, enabled: bool):
        """Enable or disable picking.
        
        Args:
            enabled: Whether picking is enabled
        """
        self.enabled = enabled
        
    def cleanup(self):
        """Clean up collision nodes."""
        for np in self.bone_colliders.values():
            np.removeNode()
        self.bone_colliders.clear()
        
        if self.picker_np:
            self.picker_np.removeNode()
