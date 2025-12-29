"""Desert-specific structure generators.

Creates natural desert features like cacti, dead bushes, and sand formations.
"""

from typing import Optional, Callable
from games.voxel_world.structures.structure_generator import StructureGenerator, Structure
import random


class CactusGenerator(StructureGenerator):
    """Generates cactus structures for desert biomes.
    
    Note: Currently uses wood blocks (green-brown). In future, could add
    dedicated cactus block type with proper texture.
    """
    
    def __init__(self, seed: int = 0):
        """Initialize cactus generator."""
        super().__init__(seed)
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        """Generate a cactus."""
        # Need flat sand
        if not self.validate_placement(x, y, z, height_callback, min_flat_radius=0):
            return None
        
        self.random.seed(x * 10000 + z + self.seed)
        cactus_variant = self.random.choice(['simple', 'branched', 'tall'])
        
        if cactus_variant == 'simple':
            return self._generate_simple_cactus(x, y, z)
        elif cactus_variant == 'branched':
            return self._generate_branched_cactus(x, y, z)
        else:
            return self._generate_tall_cactus(x, y, z)
    
    def _generate_simple_cactus(self, x: int, y: int, z: int) -> Structure:
        """Generate a simple cactus (straight column).
        
        Structure: 2-4 blocks tall, single column
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        height = self.random.randint(2, 4)
        
        for dy in range(height):
            # Use wood as placeholder for cactus
            blocks.append((x, y + dy + 1, z, "wood"))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_branched_cactus(self, x: int, y: int, z: int) -> Structure:
        """Generate a cactus with side branches.
        
        Structure: Main trunk with 1-2 side arms
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # Main trunk (3-5 blocks)
        trunk_height = self.random.randint(3, 5)
        for dy in range(trunk_height):
            blocks.append((x, y + dy + 1, z, "wood"))
        
        # Add 1-2 branches
        num_branches = self.random.randint(1, 2)
        for _ in range(num_branches):
            # Branch starts partway up trunk
            branch_y = y + self.random.randint(2, trunk_height - 1)
            
            # Branch direction
            branch_dir = self.random.choice([
                (1, 0),   # +X
                (-1, 0),  # -X
                (0, 1),   # +Z
                (0, -1)   # -Z
            ])
            
            # Horizontal arm (1-2 blocks)
            arm_length = self.random.randint(1, 2)
            for i in range(1, arm_length + 1):
                blocks.append((
                    x + branch_dir[0] * i,
                    branch_y,
                    z + branch_dir[1] * i,
                    "wood"
                ))
            
            # Vertical extension (1-2 blocks up from arm)
            extension_height = self.random.randint(1, 2)
            arm_tip_x = x + branch_dir[0] * arm_length
            arm_tip_z = z + branch_dir[1] * arm_length
            
            for dy in range(1, extension_height + 1):
                blocks.append((arm_tip_x, branch_y + dy, arm_tip_z, "wood"))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_tall_cactus(self, x: int, y: int, z: int) -> Structure:
        """Generate a tall cactus (5-7 blocks).
        
        Structure: Simple tall column
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        height = self.random.randint(5, 7)
        
        for dy in range(height):
            blocks.append((x, y + dy + 1, z, "wood"))
        
        return Structure(blocks=blocks, origin=(x, y, z))


class DeadBushGenerator(StructureGenerator):
    """Generates dead bushes for desert/wasteland biomes."""
    
    def __init__(self, seed: int = 0):
        """Initialize dead bush generator."""
        super().__init__(seed)
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        """Generate a dead bush."""
        return self._generate_dead_bush(x, y, z)
    
    def _generate_dead_bush(self, x: int, y: int, z: int) -> Structure:
        """Generate a dead bush (small, sparse wood blocks).
        
        Structure: 1-2 wood blocks representing dried twigs
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # Central block
        blocks.append((x, y + 1, z, "wood"))
        
        # Maybe one more nearby
        if self.random.random() < 0.4:
            offset = self.random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            blocks.append((x + offset[0], y + 1, z + offset[1], "wood"))
        
        return Structure(blocks=blocks, origin=(x, y, z))


class SandDuneAccentGenerator(StructureGenerator):
    """Generates small sandstone formations in deserts.
    
    Creates exposed sandstone outcrops that break up flat desert terrain.
    """
    
    def __init__(self, seed: int = 0):
        """Initialize sand dune accent generator."""
        super().__init__(seed)
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        """Generate a sandstone outcrop."""
        return self._generate_sandstone_outcrop(x, y, z)
    
    def _generate_sandstone_outcrop(self, x: int, y: int, z: int) -> Structure:
        """Generate a small sandstone formation.
        
        Structure: 2x2 or 3x3 sandstone blocks, 1-2 blocks tall
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # Size
        size = self.random.randint(2, 3)
        height = self.random.randint(1, 2)
        
        # Sandstone or red sandstone
        stone_type = self.random.choice(["sandstone", "red_sandstone"])
        
        for dy in range(height):
            for dx in range(-size // 2, size // 2 + 1):
                for dz in range(-size // 2, size // 2 + 1):
                    # Skip some edges for irregular shape
                    if abs(dx) == size // 2 and abs(dz) == size // 2:
                        if self.random.random() < 0.5:
                            continue
                    
                    blocks.append((x + dx, y + dy + 1, z + dz, stone_type))
        
        return Structure(blocks=blocks, origin=(x, y, z))
