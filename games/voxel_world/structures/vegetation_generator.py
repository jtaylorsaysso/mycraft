"""Vegetation and ground cover generators.

Creates small decorative natural features like grass clumps, flowers,
mushrooms, and other ground-level vegetation.
"""

from typing import Optional, Callable
from games.voxel_world.structures.structure_generator import StructureGenerator, Structure
import random


class VegetationGenerator(StructureGenerator):
    """Generates small vegetation features.
    
    Creates ground-level decorations:
    - Tall grass: Single leaf blocks
    - Flower patches: Colored leaf arrangements
    - Mushroom clusters: Small fungal growths
    - Ferns: Multi-block leaf patterns
    """
    
    def __init__(self, seed: int = 0, vegetation_type: str = "grass"):
        """Initialize vegetation generator.
        
        Args:
            seed: World seed
            vegetation_type: "grass", "flowers", "mushrooms", or "ferns"
        """
        super().__init__(seed)
        self.vegetation_type = vegetation_type
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        """Generate vegetation at the given position."""
        # Vegetation needs flat ground
        if not self.validate_placement(x, y, z, height_callback, min_flat_radius=0):
            return None
        
        if self.vegetation_type == "grass":
            return self._generate_tall_grass(x, y, z)
        elif self.vegetation_type == "flowers":
            return self._generate_flower_patch(x, y, z)
        elif self.vegetation_type == "mushrooms":
            return self._generate_mushroom_cluster(x, y, z)
        else:  # ferns
            return self._generate_fern(x, y, z)
    
    def _generate_tall_grass(self, x: int, y: int, z: int) -> Structure:
        """Generate tall grass (1-2 blocks tall).
        
        Structure: Single column of tall_grass blocks
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # 1 block tall (tall grass is usually 1 block high visually, double tall is rare)
        # Improving logic: mostly 1 block high
        height = 1
        if self.random.random() < 0.2:
            height = 2
            
        for dy in range(height):
            blocks.append((x, y + dy + 1, z, "tall_grass"))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_flower_patch(self, x: int, y: int, z: int) -> Structure:
        """Generate a small flower patch.
        
        Structure: 2-3 flower blocks in a small cluster
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # Center flower
        blocks.append((x, y + 1, z, "flower"))
        
        # 1-2 adjacent flowers
        num_flowers = self.random.randint(1, 2)
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        self.random.shuffle(offsets)
        
        for i in range(num_flowers):
            dx, dz = offsets[i]
            blocks.append((x + dx, y + 1, z + dz, "flower"))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_mushroom_cluster(self, x: int, y: int, z: int) -> Structure:
        """Generate a mushroom cluster.
        
        Structure: Small wood 'stems' with mushroom 'caps'
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # 1-3 mushrooms
        num_mushrooms = self.random.randint(1, 3)
        offsets = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        self.random.shuffle(offsets)
        
        for i in range(num_mushrooms):
            dx, dz = offsets[i]
            
            # Use mushroom block (directly on ground?)
            # Or stem + mushroom cap?
            # Let's simple mushroom block on ground for small mushrooms
            blocks.append((x + dx, y + 1, z + dz, "mushroom"))
             
            # If we want giant mushrooms, that's a different structure
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_fern(self, x: int, y: int, z: int) -> Structure:
        """Generate a fern (multi-block pattern).
        
        Structure: Wider spread of fern blocks
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # Center
        blocks.append((x, y + 1, z, "fern"))
        
        # Spread pattern (plus or X shape)
        if self.random.random() < 0.5:
            # Plus shape
            for dx, dz in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if self.random.random() < 0.6:
                    blocks.append((x + dx, y + 1, z + dz, "fern"))
        else:
            # X shape
            for dx, dz in [(-1, -1), (1, 1), (-1, 1), (1, -1)]:
                if self.random.random() < 0.6:
                    blocks.append((x + dx, y + 1, z + dz, "fern"))
        
        # Sometimes add second layer (tall fern logic?)
        if self.random.random() < 0.3:
            blocks.append((x, y + 2, z, "fern"))
        
        return Structure(blocks=blocks, origin=(x, y, z))


class FallenLogGenerator(StructureGenerator):
    """Generates fallen logs for forest floors.
    
    Creates horizontal wood logs in various orientations and lengths.
    """
    
    def __init__(self, seed: int = 0):
        """Initialize fallen log generator."""
        super().__init__(seed)
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        """Generate a fallen log."""
        # Need relatively flat ground
        if not self.validate_placement(x, y, z, height_callback, min_flat_radius=1):
            return None
        
        return self._generate_fallen_log(x, y, z, height_callback)
    
    def _generate_fallen_log(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Structure:
        """Generate a horizontal fallen log.
        
        Structure: 3-6 wood blocks in a line (X or Z direction)
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # Length of log
        length = self.random.randint(3, 6)
        
        # Direction (along X or Z axis)
        direction = self.random.choice(['x', 'z'])
        
        if direction == 'x':
            for i in range(length):
                # Follow terrain slightly
                terrain_y = height_callback(x + i, z)
                blocks.append((x + i, terrain_y + 1, z, "wood"))
                
                # Occasional attached leaves (moss/vines)
                if self.random.random() < 0.2:
                    blocks.append((x + i, terrain_y + 2, z, "leaves"))
        else:  # z direction
            for i in range(length):
                terrain_y = height_callback(x, z + i)
                blocks.append((x, terrain_y + 1, z + i, "wood"))
                
                if self.random.random() < 0.2:
                    blocks.append((x, terrain_y + 2, z + i, "leaves"))
        
        return Structure(blocks=blocks, origin=(x, y, z))
