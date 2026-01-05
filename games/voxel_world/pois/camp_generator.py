"""
Generates Enemy Camps.

Camps are combat encounters with loot, guarded by enemies.
"""

from typing import Tuple, Optional, Any, Dict, List
import random
import math

from engine.world.noise import get_noise
from engine.color.palette import ColorPalette
from .poi_generator import POIGenerator, POIData

class CampGenerator(POIGenerator):
    """Generates enemy camp structures."""
    
    def should_spawn_at(self, chunk_x: int, chunk_z: int) -> bool:
        """Determine if a camp spawns here."""
        # Unique noise channel for camps (different offset than shrines)
        val = get_noise(chunk_x + self.seed + 100, chunk_z + self.seed + 100, scale=0.1, octaves=1)
        
        # Slightly more common than shrines? ~10%
        return val > 0.0
        
    def get_spawn_position(
        self, 
        chunk_x: int, 
        chunk_z: int, 
        chunk_size: int,
        biome_data: Any,
        height_callback: Any
    ) -> Optional[Tuple[int, int, int]]:
        """Find a flat-ish spot for the camp."""
        center_x = chunk_size // 2
        center_z = chunk_size // 2
        
        world_x = chunk_x * chunk_size + center_x
        world_z = chunk_z * chunk_size + center_z
        
        y = height_callback(world_x, world_z)
        
        # Avoid water
        if y < 0:
            return None
            
        return (world_x, y, world_z)

    def generate(
        self, 
        x: int, 
        y: int, 
        z: int, 
        seed: int
    ) -> POIData:
        """Generate the camp structure."""
        blocks = []
        entities = []
        rng = random.Random(seed)
        
        # Pick camp-wide color palette (2-4 colors)
        all_loot_colors = ColorPalette.get_loot_color_names()
        # Seed ensures this camp always has same colors
        camp_colors = rng.sample(all_loot_colors, min(len(all_loot_colors), rng.randint(2, 4)))
        
        radius = 4
        wall_height = 2
        
        # 1. Clear/Floor Area (Circular)
        # Note: Flattening is handled partly by flatten_terrain, but we add floor blocks here
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                dist = math.sqrt(dx*dx + dz*dz)
                if dist <= radius:
                    blocks.append((x + dx, y, z + dz, "cobblestone"))
                    
                    # 2. Perimeter Wall
                    if dist >= radius - 1:
                        for h in range(1, wall_height + 1):
                            blocks.append((x + dx, y + h, z + dz, "stone_bricks"))
        
        # 3. Central Loot
        blocks.append((x, y + 1, z, "chest"))
        loot = {(x, y + 1, z): ["sword_iron", "bread", "coin_gold"]}
        
        # 4. Enemy Spawns
        # Add 3 enemies inside the camp
        for _ in range(3):
            ex = x + rng.randint(-2, 2)
            ez = z + rng.randint(-2, 2)
            # Ensure inside wall
            if math.sqrt((ex-x)**2 + (ez-z)**2) < radius - 1:
                # Assign distinct color from camp palette
                color_name = camp_colors[i % len(camp_colors)]
                # Add tuple: (type, x, y, z, color)
                entities.append(("skeleton", ex, y + 1, ez, color_name))
                
        return POIData(
            poi_type="camp_enemy",
            position=(x, y, z),
            blocks=blocks,
            entities=entities,
            loot=loot
        )
