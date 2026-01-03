"""
GLBAvatar: A skeleton-driven avatar using a GLB mesh.
"""

from typing import Dict, Optional
from panda3d.core import NodePath, Loader
from direct.showbase.Loader import Loader as DirectLoader
import gltf  # Registers .glb/.gltf loader support

from engine.animation.skeleton import HumanoidSkeleton, Bone

class GLBAvatar:
    """
    A rigged avatar that loads a GLB mesh and attaches it to a HumanoidSkeleton.
    
    If the GLB contains separate mesh nodes named after the skeleton bones (e.g. 'head', 'chest'),
    it will reparent those nodes to the corresponding skeleton bones for articulation.
    Otherwise, it attaches the entire model to the skeleton root (hips).
    """
    
    def __init__(self, parent_node: NodePath, skeleton: Optional[HumanoidSkeleton] = None, 
                 model_path: str = "engine/assets/voxel-18.glb", loader: Optional[DirectLoader | Loader] = None):
        """
        Initialize GLBAvatar.
        
        Args:
            parent_node: Parent Panda3D NodePath.
            skeleton: Optional existing skeleton. If None, creates a new HumanoidSkeleton.
            model_path: Path to the .glb file.
            loader: Panda3D loader instance. Required to load the model.
        """
        self.root = parent_node.attachNewNode("GLBAvatar")
        self.skeleton = skeleton if skeleton else HumanoidSkeleton()
        self.bone_nodes: Dict[str, NodePath] = {}
        self.model_path = model_path
        
        # We need a loader. If not provided, try to find one from base (standard in Panda3D apps)
        if loader is None:
            try:
                from direct.showbase.ShowBase import ShowBase
                base = ShowBase.getGlobalPtr()
                if base:
                    self.loader = base.loader
                else:
                    raise ValueError("No loader provided and no ShowBase global found.")
            except ImportError:
                 raise ValueError("No loader provided and cannot import ShowBase.")
        else:
            self.loader = loader

        # 1. Build the skeleton hierarchy (invisible nodes)
        self._build_bone_hierarchy(self.skeleton.root)
        
        # 2. Load the visual mesh
        try:
            self.model = self.loader.loadModel(model_path)
            if not self.model:
                 print(f"Failed to load visuals from {model_path}")
                 return
        except Exception as e:
            print(f"Error loading model {model_path}: {e}")
            return

        # 3. Attach visuals to skeleton
        self._attach_visuals()

    def _build_bone_hierarchy(self, bone: Bone, parent_node: Optional[NodePath] = None):
        """Recursively build bone hierarchy node structure."""
        effective_parent = parent_node if parent_node else self.root
        
        # Create NodePath for this bone (Joint Transform)
        bone_node = effective_parent.attachNewNode(bone.name)
        self.bone_nodes[bone.name] = bone_node
        
        # Set default local transform (T-Pose)
        t = bone.local_transform
        bone_node.setPos(t.position)
        bone_node.setHpr(t.rotation.x, t.rotation.y, t.rotation.z)
        
        # Recurse
        for child in bone.children:
            self._build_bone_hierarchy(child, bone_node)

    def _attach_visuals(self):
        """
        Traverse the loaded model. For each child matching a bone name, 
        reparent it to that bone. Any unmatched parts remain/are attached to hips (root).
        """
        # We'll check the top-level children of the loaded model
        # If we find a match, we move it.
        
        # Note: If the model is a single mesh named "voxel-18", it won't match "head", etc.
        # This loop handles decomposing the model if it was exported as separate parts.
        
        attached_parts = 0
        
        # Create a list of children to iterate safely while reparenting
        children = [child for child in self.model.getChildren()]
        
        for child in children:
            name = child.getName()
            # Clean up name (Blender sometimes adds .001, etc.)
            clean_name = name.split('.')[0]
            
            if clean_name in self.bone_nodes:
                # Found a matching bone! Reparent it.
                child.reparentTo(self.bone_nodes[clean_name])
                # Reset transform since it's now local to the bone
                child.setPos(0, 0, 0)
                child.setHpr(0, 0, 0)
                attached_parts += 1
            else:
                 # No match found for this specific part
                 pass
                 
        if attached_parts == 0:
            # Fallback: Attach everything to the root bone (hips)
            # This ensures the model follows the character's global movement at least
            print(f"GLBAvatar: No matching named parts found in {self.model_path}. Attaching full model to 'hips'.")
            self.model.reparentTo(self.bone_nodes["hips"])
            # Adjust offset if necessary (the voxel model hips are ~1.0m up)
            # If the GLB origin is at the feet, we might need to offset it down relative to hips
            # specific to this voxel-18 model?
            # For now, 0,0,0 relative to hips.
            self.model.setPos(0, 0, 0) 
        else:
            # We attached what we could. Anything remaining in self.model?
            if self.model.getNumChildren() == 0:
                self.model.removeNode() # Empty container
            else:
                # Attach remaining parts (props? unskinned mesh?) to hips
                self.model.reparentTo(self.bone_nodes["hips"])

    def cleanup(self):
        if self.root:
            self.root.removeNode()
            self.root = None
