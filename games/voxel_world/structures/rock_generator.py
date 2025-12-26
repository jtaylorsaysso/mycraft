"""Boulder and rock formation generators for rocky/mountain biomes.

Creates natural stone formations including scattered boulders, rock outcrops,
and stone spires for visual and gameplay variety.
"""

from typing import Optional, Callable
from games.voxel_world.structures.structure_generator import StructureGenerator, Structure
import random


class BoulderGenerator(StructureGenerator):
    """Generates natural boulder formations.
    
    Creates various boulder types:
    - Small boulders: 1-2 blocks (scattered rocks)
    - Medium boulders: 3x3x2 irregular shapes
    - Large boulders: 4x4x3 with overhangs
    - Boulder clusters: Groups of 2-4 small boulders
    """
    
    def __init__(self, seed: int = 0, boulder_type: str = "medium"):
        """Initialize boulder generator.
        
        Args:
            seed: World seed for deterministic generation
            boulder_type: "small", "medium", "large", or "cluster"
        """
        super().__init__(seed)
        self.boulder_type = boulder_type
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        """Generate a boulder at the given position.
        
        Args:
            x: World X coordinate
            y: World Y coordinate (ground level)
            z: World Z coordinate
            height_callback: Function to query terrain height
            
        Returns:
            Structure with boulder blocks, or None if invalid
        """
        # Less strict validation for boulders (can be on slopes)
        if not self.validate_placement(x, y, z, height_callback, min_flat_radius=0):
            return None
        
        if self.boulder_type == "small":
            return self._generate_small_boulder(x, y, z)
        elif self.boulder_type == "large":
            return self._generate_large_boulder(x, y, z)
        elif self.boulder_type == "cluster":
            return self._generate_boulder_cluster(x, y, z)
        else:  # medium
            return self._generate_medium_boulder(x, y, z)
    
    def _generate_small_boulder(self, x: int, y: int, z: int) -> Structure:
        """Generate a small boulder (1-2 blocks).
        
        Structure: Single stone block or 2-block stack
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # Randomly use mossy or regular stone
        stone_type = self.random.choice([
            "stone", "stone", "cobblestone_mossy", "andesite"
        ])
        
        # 1 or 2 blocks tall
        height = self.random.randint(1, 2)
        for dy in range(height):
            blocks.append((x, y + dy + 1, z, stone_type))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_medium_boulder(self, x: int, y: int, z: int) -> Structure:
        """Generate a medium boulder (3x3 base, irregular shape).
        
        Structure: Organic blob shape, 2-3 blocks tall
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        stone_type = self.random.choice([
            "stone", "cobblestone_mossy", "andesite", "granite"
        ])
        
        # Layer 1 (base) - 3x3 with some gaps
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                # Skip corners sometimes for irregular shape
                if abs(dx) == 1 and abs(dz) == 1:
                    if self.random.random() < 0.3:
                        continue
                
                blocks.append((x + dx, y + 1, z + dz, stone_type))
        
        # Layer 2 (middle) - smaller
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if abs(dx) + abs(dz) <= 1:  # Plus shape
                    blocks.append((x + dx, y + 2, z + dz, stone_type))
        
        # Layer 3 (top) - small cap (60% chance)
        if self.random.random() < 0.6:
            blocks.append((x, y + 3, z, stone_type))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_large_boulder(self, x: int, y: int, z: int) -> Structure:
        """Generate a large boulder (4x4 base, with overhangs).
        
        Structure: Impressive rock formation, 3-4 blocks tall
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        stone_type = self.random.choice([
            "stone", "andesite", "granite"
        ])
        
        # Layer 1 (base) - wide 4x4 with gaps
        for dx in range(-2, 2):
            for dz in range(-2, 2):
                # Skip far corners
                if abs(dx) == 2 and abs(dz) == 2:
                    continue
                blocks.append((x + dx, y + 1, z + dz, stone_type))
        
        # Layer 2 - still wide
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                blocks.append((x + dx, y + 2, z + dz, stone_type))
        
        # Layer 3 - smaller
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if abs(dx) + abs(dz) <= 2:
                    blocks.append((x + dx, y + 3, z + dz, stone_type))
        
        # Layer 4 - cap
        blocks.append((x, y + 4, z, stone_type))
        
        # Add some overhang blocks randomly
        if self.random.random() < 0.5:
            overhang_dx = self.random.choice([-1, 1])
            blocks.append((x + overhang_dx, y + 3, z, stone_type))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_boulder_cluster(self, x: int, y: int, z: int) -> Structure:
        """Generate a cluster of small boulders.
        
        Structure: 2-4 small boulders in a group
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # Number of boulders in cluster
        num_boulders = self.random.randint(2, 4)
        
        # Place boulders in a small radius
        for i in range(num_boulders):
            offset_x = self.random.randint(-2, 2)
            offset_z = self.random.randint(-2, 2)
            
            stone_type = self.random.choice([
                "stone", "cobblestone_mossy", "andesite"
            ])
            
            boulder_height = self.random.randint(1, 2)
            for dy in range(boulder_height):
                blocks.append((
                    x + offset_x,
                    y + dy + 1,
                    z + offset_z,
                    stone_type
                ))
        
        return Structure(blocks=blocks, origin=(x, y, z))


class RockFormationGenerator(StructureGenerator):
    """Generates dramatic rock formations.
    
    Creates natural geological features:
    - Stone spires: Tall narrow columns
    - Rock arches: Natural bridges (future)
    - Outcrops: Layered rock shelves
    """
    
    def __init__(self, seed: int = 0, formation_type: str = "spire"):
        """Initialize rock formation generator.
        
        Args:
            seed: World seed
            formation_type: "spire", "outcrop", or "pillar"
        """
        super().__init__(seed)
        self.formation_type = formation_type
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        """Generate a rock formation."""
        if self.formation_type == "spire":
            return self._generate_spire(x, y, z)
        elif self.formation_type == "outcrop":
            return self._generate_outcrop(x, y, z)
        else:  # pillar
            return self._generate_pillar(x, y, z)
    
    def _generate_spire(self, x: int, y: int, z: int) -> Structure:
        """Generate a stone spire (tall, narrow).
        
        Structure: 5-8 blocks tall, tapers toward top
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        height = self.random.randint(5, 8)
        stone_type = "stone"
        
        # Wide base
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                blocks.append((x + dx, y + 1, z + dz, stone_type))
        
        # Narrow shaft
        for dy in range(2, height - 1):
            # Plus shape
            blocks.append((x, y + dy, z, stone_type))
            blocks.append((x + 1, y + dy, z, stone_type))
            blocks.append((x - 1, y + dy, z, stone_type))
            blocks.append((x, y + dy, z + 1, stone_type))
            blocks.append((x, y + dy, z - 1, stone_type))
        
        # Pointed top
        blocks.append((x, y + height - 1, z, stone_type))
        blocks.append((x, y + height, z, stone_type))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_outcrop(self, x: int, y: int, z: int) -> Structure:
        """Generate a rock outcrop (layered, shelf-like).
        
        Structure: Wide, flat, stepped layers
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        stone_type = self.random.choice(["stone", "andesite", "granite"])
        
        # Layer 1 (widest)
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) <= 2 and abs(dz) <= 2:
                    blocks.append((x + dx, y + 1, z + dz, stone_type))
        
        # Layer 2 (offset)
        for dx in range(-1, 3):
            for dz in range(-1, 2):
                blocks.append((x + dx, y + 2, z + dz, stone_type))
        
        # Layer 3 (top shelf)
        for dx in range(0, 2):
            for dz in range(-1, 2):
                blocks.append((x + dx, y + 3, z + dz, stone_type))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_pillar(self, x: int, y: int, z: int) -> Structure:
        """Generate a stone pillar (short, thick column).
        
        Structure: 3x3 base, 3-5 blocks tall
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        height = self.random.randint(3, 5)
        stone_type = "stone"
        
        # Consistent 3x3 pillar
        for dy in range(height):
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    # Skip corners for octagonal shape
                    if abs(dx) == 1 and abs(dz) == 1:
                        continue
                    blocks.append((x + dx, y + dy + 1, z + dz, stone_type))
        
        return Structure(blocks=blocks, origin=(x, y, z))
