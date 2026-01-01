"""
Generates Challenge Shrines.

Shrines are tall, visible structures that offer movement or combat challenges.
"""

from typing import Tuple, Optional, Any, Dict
import random

from engine.world.noise import get_noise
from .poi_generator import POIGenerator, POIData

class ShrineGenerator(POIGenerator):
    """Generates tall shrine structures."""
    
    def should_spawn_at(self, chunk_x: int, chunk_z: int) -> bool:
        """Determine if a shrine spawns here.
        
        Uses noise for distribution (rare).
        """
        # Unique noise channel for shrines
        # Scale 0.1 ensures they are somewhat spread out
        val = get_noise(chunk_x + self.seed, chunk_z + self.seed, scale=0.1, octaves=1)
        
        # ~10% chance per chunk if conditions meet, but we control frequency 
        # in the main generator anyway. This is a secondary check.
        return val > 0.0
        
    def get_spawn_position(
        self, 
        chunk_x: int, 
        chunk_z: int, 
        chunk_size: int,
        biome_data: Any, # List[List[Biome]]
        height_callback: Any
    ) -> Optional[Tuple[int, int, int]]:
        """Find a flat-ish spot for the shrine."""
        center_x = chunk_size // 2
        center_z = chunk_size // 2
        
        world_x = chunk_x * chunk_size + center_x
        world_z = chunk_z * chunk_size + center_z
        
        # Determine base height
        y = height_callback(world_x, world_z)
        
        # Basic check: Don't spawn underwater
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
        """Generate the shrine structure."""
        blocks = []
        rng = random.Random(seed)
        
        # Shrine visual style (stone bricks)
        base_block = "stone_bricks"
        pillar_block = "stone" 
        accent_block = "planks_oak"
        
        # Dimensions
        base_radius = 2
        pillar_height = 10 + rng.randint(0, 4)
        
        # 1. Base Platform
        # Generate relative to (x, y, z)
        # Note: We return WORLD coordinates in the blocks list, or relative? 
        # POIData docstring says "relative to world", which implies world coordinates.
        # Let's stick to world coordinates for simplicity in placement.
        
        for dx in range(-base_radius, base_radius + 1):
            for dz in range(-base_radius, base_radius + 1):
                # Simple platform
                blocks.append((x + dx, y, z + dz, base_block))
                
                # Corner pillars
                if abs(dx) == base_radius and abs(dz) == base_radius:
                     blocks.append((x + dx, y + 1, z + dz, pillar_block))
                     blocks.append((x + dx, y + 2, z + dz, "torch")) # Mock torch
        
        # 2. Central Pillar
        for h in range(1, pillar_height):
            blocks.append((x, y + h, z, pillar_block))
            
            # Decoration rings
            if h % 4 == 0:
                blocks.append((x + 1, y + h, z, accent_block))
                blocks.append((x - 1, y + h, z, accent_block))
                blocks.append((x, y + h, z + 1, accent_block))
                blocks.append((x, y + h, z - 1, accent_block))
        
        # 3. Top Marker (Glowing if possible, for now just a distinctive block)
        blocks.append((x, y + pillar_height, z, "gold_block")) # Placeholder for glow
        
        # 4. Loot Chest
        loot_pos = (x, y + 1, z - 1)
        loot = {loot_pos: ["potion_health", "coin_gold"]} # Placeholder loot
        blocks.append((loot_pos[0], loot_pos[1], loot_pos[2], "chest"))

        return POIData(
            poi_type="shrine_challenge",
            position=(x, y, z),
            blocks=blocks,
            entities=[],
            loot=loot
        )
