"""Animation registry for centralized clip management.

Provides a single source of truth for all animation clips in the engine,
with support for JSON serialization and hot-reloading.
"""

from typing import Dict, List, Optional
from pathlib import Path
import json

from engine.animation.core import AnimationClip
from engine.animation.combat import CombatClip


class AnimationRegistry:
    """Central registry for all animation clips.
    
    Manages both procedural and data-driven animation clips,
    enabling editor discovery and hot-reload functionality.
    """
    
    def __init__(self):
        self.clips: Dict[str, AnimationClip] = {}
        self.combat_clips: Dict[str, CombatClip] = {}
        
    def register_clip(self, clip: AnimationClip):
        """Register an animation clip.
        
        Args:
            clip: AnimationClip to register
        """
        self.clips[clip.name] = clip
        
    def register_combat_clip(self, clip: CombatClip):
        """Register a combat animation clip.
        
        Args:
            clip: CombatClip to register
        """
        self.combat_clips[clip.name] = clip
        # Also register in base clips dict for general access
        self.clips[clip.name] = clip
        
    def get_clip(self, name: str) -> Optional[AnimationClip]:
        """Get clip by name.
        
        Args:
            name: Clip name
            
        Returns:
            AnimationClip if found, None otherwise
        """
        return self.clips.get(name)
    
    def get_combat_clip(self, name: str) -> Optional[CombatClip]:
        """Get combat clip by name.
        
        Args:
            name: Clip name
            
        Returns:
            CombatClip if found, None otherwise
        """
        return self.combat_clips.get(name)
        
    def list_clips(self) -> List[str]:
        """List all registered clip names.
        
        Returns:
            List of clip names
        """
        return list(self.clips.keys())
    
    def list_combat_clips(self) -> List[str]:
        """List all registered combat clip names.
        
        Returns:
            List of combat clip names
        """
        return list(self.combat_clips.keys())
    
    def save_to_json(self, name: str, path: Path):
        """Save a clip to JSON file.
        
        Args:
            name: Clip name to save
            path: Output file path
        """
        clip = self.clips.get(name)
        if not clip:
            raise ValueError(f"Clip '{name}' not found in registry")
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize clip
        # Use AnimationClip.to_dict explicitly to get base fields,
        # as CombatClip.to_dict stores only metadata.
        data = AnimationClip.to_dict(clip)
        
        # Add combat metadata if applicable
        if name in self.combat_clips:
            combat_clip = self.combat_clips[name]
            data['combat_metadata'] = combat_clip.to_dict()
        
        # Write to file
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_json(self, path: Path) -> AnimationClip:
        """Load a clip from JSON file.
        
        Args:
            path: JSON file path
            
        Returns:
            Loaded AnimationClip
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Deserialize base clip
        clip = AnimationClip.from_dict(data)
        
        # Check for combat metadata
        if 'combat_metadata' in data:
            combat_clip = CombatClip.from_dict_metadata(clip, data['combat_metadata'])
            return combat_clip
        
        return clip
    
    def reload_from_json(self, path: Path):
        """Reload a clip from JSON and update registry.
        
        Args:
            path: JSON file path
        """
        clip = self.load_from_json(path)
        
        if isinstance(clip, CombatClip):
            self.register_combat_clip(clip)
        else:
            self.register_clip(clip)
    
    def scan_directory(self, directory: Path):
        """Scan directory for JSON animation files and load them.
        
        Args:
            directory: Directory to scan
        """
        if not directory.exists():
            return
        
        for json_file in directory.rglob('*.json'):
            try:
                self.reload_from_json(json_file)
            except Exception as e:
                print(f"Failed to load animation from {json_file}: {e}")


# Global registry instance
_global_registry: Optional[AnimationRegistry] = None


def get_animation_registry() -> AnimationRegistry:
    """Get the global animation registry instance.
    
    Returns:
        Global AnimationRegistry
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AnimationRegistry()
    return _global_registry
