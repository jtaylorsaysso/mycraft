
from typing import Optional, Tuple, Any, Dict, List
import random
from engine.assets.manager import AssetManager
from engine.world.noise import get_noise
from .poi_generator import POIGenerator, POIData

class TemplatePOIGenerator(POIGenerator):
    """POI generator that uses template files instead of code."""
    
    def __init__(self, seed: int, template_name: str):
        super().__init__(seed)
        self.template_name = template_name
        self.template = AssetManager().load_poi_template(template_name)
        
    def should_spawn_at(self, chunk_x: int, chunk_z: int) -> bool:
        """Use noise-based spawning like other generators."""
        # Configurable via template metadata? For now use hash of name as offset
        offset = hash(self.template_name) % 1000
        
        # Use noise
        val = get_noise(
            chunk_x + self.seed + offset, 
            chunk_z + self.seed + offset, 
            scale=0.05, 
            octaves=1
        )
        
        # Probability threshold ~5%
        return val > 0.8
        
    def get_spawn_position(
        self, 
        chunk_x: int, 
        chunk_z: int, 
        chunk_size: int,
        biome_data: Any,
        height_callback: Any
    ) -> Optional[Tuple[int, int, int]]:
        """Check biome affinity and find suitable position."""
        
        # Check biome affinity
        # biome_data is likely an object or dict with 'name' property
        if self.template.biome_affinity:
            # Handle different biome data structures (object vs dict)
            biome_name = str(biome_data).lower()
            if hasattr(biome_data, 'name'):
                biome_name = biome_data.name.lower()
            
            # Simple check: is one of the affinities in the biome name?
            # e.g. "forest" in "dark_forest"
            match = False
            for aff in self.template.biome_affinity:
                if aff.lower() == "any" or aff.lower() in biome_name:
                    match = True
                    break
            
            if not match:
                return None
        
        # Standard center-of-chunk placement
        center_x = chunk_size // 2
        center_z = chunk_size // 2
        
        world_x = chunk_x * chunk_size + center_x
        world_z = chunk_z * chunk_size + center_z
        
        y = height_callback(world_x, world_z)
        
        # Basic water check
        if y < 0: # Sea level assumed 0
             return None
             
        return (world_x, y, world_z)
        
    def generate(
        self, 
        x: int, 
        y: int, 
        z: int, 
        seed: int
    ) -> POIData:
        """Generate POI from template."""
        
        # Offset template blocks to world position
        # Template blocks are relative to center (0,0,0)
        world_blocks: List[Tuple[int, int, int, str]] = [
            (x + bx, y + by, z + bz, block_name)
            for bx, by, bz, block_name in self.template.blocks
        ]
        
        # Offset entities
        # Entities stored as dicts in template
        world_entities: List[Tuple[str, int, int, int]] = []
        for e in self.template.entities:
            # Safe access
            etype = e.get("type", "unknown")
            ex = e.get("x", 0)
            ey = e.get("y", 0)
            ez = e.get("z", 0)
            world_entities.append((etype, x + ex, y + ey, z + ez))
        
        # Offset loot
        world_loot: Dict[Tuple[int, int, int], List[str]] = {}
        for lp in self.template.loot_points:
            lx = lp.get("x", 0)
            ly = lp.get("y", 0)
            lz = lp.get("z", 0)
            items = lp.get("items", [])
            world_loot[(x + lx, y + ly, z + lz)] = items
        
        return POIData(
            poi_type=self.template.poi_type,
            position=(x, y, z),
            blocks=world_blocks,
            entities=world_entities,
            loot=world_loot
        )
