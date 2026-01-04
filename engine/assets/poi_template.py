
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional

@dataclass
class POITemplate:
    """Serializable POI template data."""
    
    # Metadata
    name: str
    poi_type: str  # "shrine", "camp", "dungeon", "custom"
    version: int = 1
    
    # Placement hints
    biome_affinity: List[str] = field(default_factory=list)  # Empty = any biome
    min_clear_radius: int = 5  # Terrain flattening radius
    
    # Content
    # (x, y, z, block_name) - relative to center
    blocks: List[Tuple[int, int, int, str]] = field(default_factory=list)
    
    # [{type, x, y, z, properties}]
    entities: List[Dict[str, Any]] = field(default_factory=list)
    
    # [{x, y, z, items: [...]}]
    loot_points: List[Dict[str, Any]] = field(default_factory=list)
    
    # Bounds (auto-calculated or manual)
    bounds_min: Tuple[int, int, int] = (0, 0, 0)
    bounds_max: Tuple[int, int, int] = (0, 0, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "name": self.name,
            "poi_type": self.poi_type,
            "version": self.version,
            "biome_affinity": self.biome_affinity,
            "min_clear_radius": self.min_clear_radius,
            "blocks": self.blocks,
            "entities": self.entities,
            "loot_points": self.loot_points,
            "bounds_min": self.bounds_min,
            "bounds_max": self.bounds_max
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POITemplate":
        """Deserialize from dict."""
        return cls(
            name=data.get("name", "Untitled"),
            poi_type=data.get("poi_type", "custom"),
            version=data.get("version", 1),
            biome_affinity=data.get("biome_affinity", []),
            min_clear_radius=data.get("min_clear_radius", 5),
            blocks=[tuple(b) for b in data.get("blocks", [])], # Ensure tuples
            entities=data.get("entities", []),
            loot_points=data.get("loot_points", []),
            bounds_min=tuple(data.get("bounds_min", (0, 0, 0))),
            bounds_max=tuple(data.get("bounds_max", (0, 0, 0)))
        )
        
    def calculate_bounds(self):
        """Recalculate bounds from blocks."""
        if not self.blocks:
            self.bounds_min = (0, 0, 0)
            self.bounds_max = (0, 0, 0)
            return

        xs = [b[0] for b in self.blocks]
        ys = [b[1] for b in self.blocks]
        zs = [b[2] for b in self.blocks]
        
        self.bounds_min = (min(xs), min(ys), min(zs))
        self.bounds_max = (max(xs), max(ys), max(zs))
