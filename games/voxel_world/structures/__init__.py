"""Structure generation for world decoration.

This module provides procedural structure generation (trees, boulders, etc.)
for adding visual diversity to biomes.
"""

from games.voxel_world.structures.structure_generator import StructureGenerator
from games.voxel_world.structures.tree_generator import TreeGenerator
from games.voxel_world.structures.rock_generator import (
    BoulderGenerator,
    RockFormationGenerator
)
from games.voxel_world.structures.vegetation_generator import (
    VegetationGenerator,
    FallenLogGenerator
)
from games.voxel_world.structures.desert_generator import (
    CactusGenerator,
    DeadBushGenerator,
    SandDuneAccentGenerator
)

__all__ = [
    'StructureGenerator',
    'TreeGenerator',
    'BoulderGenerator',
    'RockFormationGenerator',
    'VegetationGenerator',
    'FallenLogGenerator',
    'CactusGenerator',
    'DeadBushGenerator',
    'SandDuneAccentGenerator'
]

