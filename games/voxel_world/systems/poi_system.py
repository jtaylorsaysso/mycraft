"""POI (Point of Interest) placement and management system.

Handles sparse placement of special structures like Challenge Shrines
with minimum spacing requirements and metadata tracking.
"""

from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
import os
from games.voxel_world.structures.shrine_structures import (
    PlainsAltarGenerator,
    ForestClearingGenerator,
    MountainPeakGenerator,
    CanyonOutcropGenerator,
    RiversideRuinsGenerator
)
from games.voxel_world.utils.noise import get_noise


@dataclass
class POIMetadata:
    """Metadata for a placed POI."""
    variant: str  # "plains_altar", "forest_clearing", etc.
    position: Tuple[int, int, int]  # World coordinates (x, y, z)
    chunk_coords: Tuple[int, int]  # Chunk coordinates (cx, cz)
    # Future: enemy_spawns, chest_state, discovered, etc.


class POIRegistry:
    """Tracks all placed POIs for persistence and gameplay."""
    
    def __init__(self):
        self.pois: Dict[Tuple[int, int], POIMetadata] = {}  # chunk_coords -> POI
        
    def register_poi(self, poi: POIMetadata):
        """Register a POI at a chunk location."""
        self.pois[poi.chunk_coords] = poi
        
    def get_poi_at_chunk(self, chunk_x: int, chunk_z: int) -> Optional[POIMetadata]:
        """Get POI metadata for a chunk, if any."""
        return self.pois.get((chunk_x, chunk_z))
        
    def has_poi_at_chunk(self, chunk_x: int, chunk_z: int) -> bool:
        """Check if a chunk contains a POI."""
        return (chunk_x, chunk_z) in self.pois


class POISystem:
    """Manages POI placement during world generation."""
    
    # Minimum spacing between POIs (in chunks)
    MIN_SPACING = 10
    
    # Sparse placement probability (~1% of chunks)
    PLACEMENT_DENSITY = 0.01
    PLACEMENT_SCALE = 0.05
    
    def __init__(self, world_seed: int = 0):
        self.world_seed = world_seed
        self.registry = POIRegistry()
        
        # Generator instances (lazy init)
        self._generators = {
            "plains_altar": PlainsAltarGenerator(seed=world_seed),
            "forest_clearing": ForestClearingGenerator(seed=world_seed),
            "mountain_peak": MountainPeakGenerator(seed=world_seed),
            "canyon_outcrop": CanyonOutcropGenerator(seed=world_seed),
            "riverside_ruins": RiversideRuinsGenerator(seed=world_seed)
        }
        
        # Load template-based generators
        self._load_template_generators()
        
    def should_place_poi_at_chunk(self, chunk_x: int, chunk_z: int) -> bool:
        """Determine if a POI should be placed at this chunk using noise."""
        # Use noise for sparse, natural distribution
        noise_value = get_noise(
            chunk_x + self.world_seed * 1000,
            chunk_z + self.world_seed * 1000,
            scale=self.PLACEMENT_SCALE,
            octaves=2
        )
        normalized = (noise_value + 1.0) / 2.0
        
        # Only place if noise exceeds threshold
        if normalized < (1.0 - self.PLACEMENT_DENSITY):
            return False
            
        # Check minimum spacing (no POIs within MIN_SPACING chunks)
        for dx in range(-self.MIN_SPACING, self.MIN_SPACING + 1):
            for dz in range(-self.MIN_SPACING, self.MIN_SPACING + 1):
                if dx == 0 and dz == 0:
                    continue
                if self.registry.has_poi_at_chunk(chunk_x + dx, chunk_z + dz):
                    return False
                    
        return True
        
    def select_poi_variant(self, chunk_x: int, chunk_z: int, biome_name: str) -> Optional[str]:
        """Select appropriate POI variant based on biome."""
        # Map biomes to shrine types
        biome_to_shrine = {
            "plains": "plains_altar",
            "forest": "forest_clearing",
            "mountain": "mountain_peak",
            "canyon": "canyon_outcrop",
            "river": "riverside_ruins",
            "swamp": "riverside_ruins",  # Swamps also get ruins
            # Others: no POI or fallback
        }
        
        return biome_to_shrine.get(biome_name.lower())
        
    def get_poi_generator(self, variant: str):
        """Get the structure generator for a POI variant."""
        return self._generators.get(variant)

    def _load_template_generators(self):
        """Scan for .mcp template files and create generators."""
        from engine.assets.manager import AssetManager
        from games.voxel_world.pois.template_poi_generator import TemplatePOIGenerator
        from engine.core.logger import get_logger
        
        logger = get_logger(__name__)
        am = AssetManager()
        
        # Ensure directory exists to avoid errors on first run
        if not os.path.exists(os.path.join(am.asset_dir, "pois")):
            return
            
        for template_name in am.list_poi_templates():
            try:
                # Avoid overwriting hardcoded ones unless intentional?
                # Let's allow overwrite for customization
                gen = TemplatePOIGenerator(self.world_seed, template_name)
                # Register by template name (e.g. "my_shrine")
                self._generators[template_name] = gen
                
                # Also, if it has a biome affinity, we might want to register it for that biome logic?
                # Currently select_poi_variant is hardcoded map.
                # TODO: Make select_poi_variant dynamic based on available generators.
                
                logger.debug(f"Loaded POI template: {template_name}")
            except Exception as e:
                logger.warning(f"Failed to load POI template {template_name}: {e}")
