"""Tree structure generation for forest and swamp biomes.

Generates various tree types with configurable sizes and shapes.
"""

from typing import Optional, Callable
from games.voxel_world.structures.structure_generator import StructureGenerator, Structure
import random


class TreeGenerator(StructureGenerator):
    """Generates tree structures with trunks and foliage.
    
    Supports multiple tree variants:
    - Standard trees (forest): 4-6 blocks tall, leafy canopy
    - Oak-style trees: Short and wide
    - Pine/spruce: Tall and narrow, conical shape
    - Dead trees (swamp): Just trunks, no leaves
    - Bushes: Single leaf block at ground level
    """
    
    def __init__(self, seed: int = 0, tree_type: str = "standard"):
        """Initialize tree generator.
        
        Args:
            seed: World seed for deterministic generation
            tree_type: Type of tree ("standard", "oak", "pine", "dead", "bush")
        """
        super().__init__(seed)
        self.tree_type = tree_type
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        """Generate a tree at the given position.
        
        Args:
            x: World X coordinate (tree center)
            y: World Y coordinate (ground level)
            z: World Z coordinate (tree center)
            height_callback: Function to query terrain height
            
        Returns:
            Structure with tree blocks, or None if invalid placement
        """
        # Validate placement (check for flat ground)
        if not self.validate_placement(x, y, z, height_callback, min_flat_radius=1):
            return None
        
        # Generate based on tree type
        if self.tree_type == "bush":
            return self._generate_bush(x, y, z)
        elif self.tree_type == "dead":
            return self._generate_dead_tree(x, y, z)
        elif self.tree_type == "pine":
            return self._generate_pine_tree(x, y, z)
        elif self.tree_type == "oak":
            return self._generate_oak_tree(x, y, z)
        else:  # standard
            return self._generate_standard_tree(x, y, z)
    
    def _generate_standard_tree(self, x: int, y: int, z: int) -> Structure:
        """Generate a standard tree (medium height, round canopy).
        
        Structure:
        - Trunk: 4-6 blocks tall
        - Canopy: 3x3x3 sphere of leaves around top
        """
        blocks = []
        
        # Randomize trunk height (4-6 blocks)
        self.random.seed(x * 10000 + z + self.seed)
        trunk_height = self.random.randint(4, 6)
        
        # Build trunk
        for dy in range(trunk_height):
            blocks.append((x, y + dy + 1, z, "wood"))
        
        # Build canopy (sphere of leaves)
        canopy_y = y + trunk_height
        for dx in range(-2, 3):
            for dy in range(-1, 3):
                for dz in range(-2, 3):
                    # Skip center (trunk passes through)
                    if dx == 0 and dz == 0 and dy <= 0:
                        continue
                    
                    # Spherical shape (Manhattan distance)
                    distance = abs(dx) + abs(dy) + abs(dz)
                    if distance <= 3:
                        # Add some randomness to canopy shape
                        if distance == 3 and self.random.random() < 0.3:
                            continue  # 30% chance to skip outer leaves
                        
                        blocks.append((
                            x + dx,
                            canopy_y + dy,
                            z + dz,
                            "leaves"
                        ))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_oak_tree(self, x: int, y: int, z: int) -> Structure:
        """Generate an oak-style tree (short and wide).
        
        Structure:
        - Trunk: 3-4 blocks tall
        - Canopy: Wide, flat-topped sphere
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        trunk_height = self.random.randint(3, 4)
        
        # Trunk
        for dy in range(trunk_height):
            blocks.append((x, y + dy + 1, z, "wood"))
        
        # Wide, flat canopy
        canopy_y = y + trunk_height
        for dx in range(-2, 3):
            for dy in range(-1, 2):  # Flatter than standard
                for dz in range(-2, 3):
                    if dx == 0 and dz == 0 and dy <= 0:
                        continue
                    
                    # Wider horizontal spread
                    if abs(dx) <= 2 and abs(dz) <= 2:
                        blocks.append((
                            x + dx,
                            canopy_y + dy,
                            z + dz,
                            "leaves"
                        ))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_pine_tree(self, x: int, y: int, z: int) -> Structure:
        """Generate a pine/spruce tree (tall and narrow, conical).
        
        Structure:
        - Trunk: 6-8 blocks tall
        - Canopy: Conical shape (narrow at top, wider at bottom)
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        trunk_height = self.random.randint(6, 8)
        
        # Trunk
        for dy in range(trunk_height):
            blocks.append((x, y + dy + 1, z, "wood"))
        
        # Conical canopy (get wider toward bottom)
        canopy_y = y + trunk_height
        for layer in range(4):  # 4 layers of leaves
            dy = -layer
            radius = min(layer, 2)  # Max radius of 2
            
            for dx in range(-radius, radius + 1):
                for dz in range(-radius, radius + 1):
                    if dx == 0 and dz == 0:
                        continue  # Trunk passes through
                    
                    # Diamond shape (not square)
                    if abs(dx) + abs(dz) <= radius:
                        blocks.append((
                            x + dx,
                            canopy_y + dy,
                            z + dz,
                            "leaves"
                        ))
        
        # Top leaf
        blocks.append((x, canopy_y + 1, z, "leaves"))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_dead_tree(self, x: int, y: int, z: int) -> Structure:
        """Generate a dead tree (trunk only, no leaves).
        
        Structure:
        - Trunk: 3-5 blocks tall
        - No canopy
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        trunk_height = self.random.randint(3, 5)
        
        # Just trunk
        for dy in range(trunk_height):
            blocks.append((x, y + dy + 1, z, "wood"))
        
        return Structure(blocks=blocks, origin=(x, y, z))
    
    def _generate_bush(self, x: int, y: int, z: int) -> Structure:
        """Generate a small bush (ground-level leaves).
        
        Structure:
        - Single layer of leaves at ground level (2x2 or 3x3)
        """
        blocks = []
        self.random.seed(x * 10000 + z + self.seed)
        
        # Random size (2x2 or 3x3)
        radius = 1 if self.random.random() < 0.5 else 1
        
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                # Skip some edges for irregular shape
                if abs(dx) == radius and abs(dz) == radius:
                    if self.random.random() < 0.5:
                        continue
                
                blocks.append((x + dx, y + 1, z + dz, "leaves"))
        
        return Structure(blocks=blocks, origin=(x, y, z))
