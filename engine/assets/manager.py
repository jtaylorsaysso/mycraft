import json
import os
from typing import Dict, Any, Optional, Union, List
from panda3d.core import NodePath

from engine.animation.skeleton import Skeleton, HumanoidSkeleton
from engine.animation.voxel_avatar import VoxelAvatar
from engine.animation.core import AnimationClip
from engine.assets.poi_template import POITemplate

class AssetManager:
    """Manages loading and saving of game assets (avatars, animations)."""
    
    def __init__(self, asset_dir: str = "assets"):
        """Initialize asset manager.
        
        Args:
            asset_dir: Base directory for assets
        """
        self.asset_dir = asset_dir
        
    def ensure_dir(self, subdir: str = ""):
        """Ensure asset directory exists."""
        path = os.path.join(self.asset_dir, subdir)
        os.makedirs(path, exist_ok=True)
        
    def get_full_path(self, filename: str, extension: str) -> str:
        """Get full path for an asset file."""
        if not filename.endswith(extension):
            filename += extension
        return os.path.join(self.asset_dir, filename)

    def save_avatar(self, avatar: VoxelAvatar, filename: str):
        """Save avatar to .mca file.
        
        Args:
            avatar: VoxelAvatar instance to save
            filename: Target filename (e.g. "hero_v1")
        """
        self.ensure_dir()
        path = self.get_full_path(filename, ".mca")
        
        data = avatar.to_dict()
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_avatar(self, filename: str, parent_node: NodePath) -> VoxelAvatar:
        """Load avatar from .mca file.
        
        Args:
            filename: Name of file to load
            parent_node: Parent Panda3D node for the avatar
            
        Returns:
            VoxelAvatar instance
        """
        path = self.get_full_path(filename, ".mca")
        
        with open(path, 'r') as f:
            data = json.load(f)
            
        # Validate type
        if data.get("type") != "avatar":
            raise ValueError(f"File {filename} is not a valid avatar file")
            
        return VoxelAvatar.from_dict(data, parent_node)

    def save_animation_clip(self, clip: AnimationClip, filename: str):
        """Save animation clip to .mcc file."""
        self.ensure_dir()
        path = self.get_full_path(filename, ".mcc")
        
        data = clip.to_dict()
        data["type"] = "animation_clip" # Add type tag
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_animation_clip(self, filename: str) -> AnimationClip:
        """Load animation clip from .mcc file."""
        path = self.get_full_path(filename, ".mcc")
        
        with open(path, 'r') as f:
            data = json.load(f)
            
        return AnimationClip.from_dict(data)

    def save_poi_template(self, template: POITemplate, filename: str):
        """Save POI template to .mcp file."""
        self.ensure_dir("pois")
        path = self.get_full_path(os.path.join("pois", filename), ".mcp")
        
        with open(path, 'w') as f:
            json.dump(template.to_dict(), f, indent=2)
            
    def load_poi_template(self, filename: str) -> POITemplate:
        """Load POI template from .mcp file."""
        # Check if filename already includes directory or extension helper needed?
        # get_full_path handles extension, but we need to ensure it looks in pois/ if not provided
        if "pois" not in filename and not os.path.exists(os.path.join(self.asset_dir, filename)):
             filename = os.path.join("pois", filename)
             
        path = self.get_full_path(filename, ".mcp")
        
        with open(path, 'r') as f:
            data = json.load(f)
        return POITemplate.from_dict(data)
        
    def list_poi_templates(self) -> List[str]:
        """List available POI template files."""
        pois_dir = os.path.join(self.asset_dir, "pois")
        if not os.path.exists(pois_dir):
            return []
        return [f[:-4] for f in os.listdir(pois_dir) if f.endswith(".mcp")]
