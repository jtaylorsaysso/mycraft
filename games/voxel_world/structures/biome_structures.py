"""Biome-specific structure configuration.

This module defines which structures should appear in each biome,
along with their densities and spawn parameters.
"""

# BIOME STRUCTURE MAPPINGS
# Format: biome_name -> [(GeneratorClass, density, scale, kwargs), ...]
#
# density: Probability threshold (0.0-1.0). Higher = more structures. Recommend 0.02-0.15
# scale: Noise scale. Lower = larger clusters, higher = more scattered. Recommend 0.1-0.5
# kwargs: Additional parameters for generator (e.g., tree_type, boulder_type)

BIOME_STRUCTURES = {
    "forest": [
        # Dense tree coverage with variety
        ("TreeGenerator", {
            "density": 0.08,
            "scale": 0.3,
            "spacing": 3,
            "tree_type": "standard"
        }),
        ("TreeGenerator", {
            "density": 0.03,
            "scale": 0.25,
            "spacing": 3,
            "tree_type": "oak"
        }),
        # Ground cover
        ("VegetationGenerator", {
            "density": 0.2,
            "scale": 0.5,
            "spacing": 2,
            "vegetation_type": "grass"
        }),
        ("VegetationGenerator", {
            "density": 0.05,
            "scale": 0.4,
            "spacing": 3,
            "vegetation_type": "ferns"
        }),
        ("VegetationGenerator", {
            "density": 0.03,
            "scale": 0.3,
            "spacing": 4,
            "vegetation_type": "flowers"
        }),
        ("VegetationGenerator", {
            "density": 0.02,
            "scale": 0.2,
            "spacing": 4,
            "vegetation_type": "mushrooms"
        }),
        # Fallen logs
        ("FallenLogGenerator", {
            "density": 0.015,
            "scale": 0.15,
            "spacing": 5
        }),
    ],
    
    "plains": [
        # Sparse trees
        ("TreeGenerator", {
            "density": 0.01,
            "scale": 0.2,
            "spacing": 5,
            "tree_type": "oak"
        }),
        # Lots of grass
        ("VegetationGenerator", {
            "density": 0.25,
            "scale": 0.6,
            "spacing": 2,
            "vegetation_type": "grass"
        }),
        # Flower patches
        ("VegetationGenerator", {
            "density": 0.08,
            "scale": 0.4,
            "spacing": 3,
            "vegetation_type": "flowers"
        }),
        # Occasional bushes
        ("TreeGenerator", {
            "density": 0.03,
            "scale": 0.3,
            "spacing": 3,
            "tree_type": "bush"
        }),
    ],
    
    "rocky": [
        # Boulder fields
        ("BoulderGenerator", {
            "density": 0.06,
            "scale": 0.25,
            "spacing": 3,
            "boulder_type": "medium"
        }),
        ("BoulderGenerator", {
            "density": 0.03,
            "scale": 0.2,
            "spacing": 4,
            "boulder_type": "large"
        }),
        ("BoulderGenerator", {
            "density": 0.08,
            "scale": 0.3,
            "spacing": 2,
            "boulder_type": "small"
        }),
        # Rock formations
        ("RockFormationGenerator", {
            "density": 0.02,
            "scale": 0.15,
            "spacing": 5,
            "formation_type": "pillar"
        }),
    ],
    
    "mountain": [
        # Sparse pine trees at lower elevations
        ("TreeGenerator", {
            "density": 0.02,
            "scale": 0.2,
            "spacing": 4,
            "tree_type": "pine"
        }),
        # Dramatic rock formations
        ("RockFormationGenerator", {
            "density": 0.04,
            "scale": 0.2,
            "spacing": 4,
            "formation_type": "spire"
        }),
        ("RockFormationGenerator", {
            "density": 0.03,
            "scale": 0.18,
            "spacing": 4,
            "formation_type": "outcrop"
        }),
        # Large boulders
        ("BoulderGenerator", {
            "density": 0.05,
            "scale": 0.25,
            "spacing": 3,
            "boulder_type": "large"
        }),
        ("BoulderGenerator", {
            "density": 0.04,
            "scale": 0.22,
            "spacing": 3,
            "boulder_type": "cluster"
        }),
    ],
    
    "desert": [
        # Cacti
        ("CactusGenerator", {
            "density": 0.05,
            "scale": 0.3,
            "spacing": 3
        }),
        # Dead bushes (sparse)
        ("DeadBushGenerator", {
            "density": 0.08,
            "scale": 0.4,
            "spacing": 2
        }),
        # Sandstone outcrops
        ("SandDuneAccentGenerator", {
            "density": 0.03,
            "scale": 0.2,
            "spacing": 4
        }),
    ],
    
    "canyon": [
        # Rock formations on mesa tops
        ("RockFormationGenerator", {
            "density": 0.03,
            "scale": 0.2,
            "spacing": 4,
            "formation_type": "spire"
        }),
        # Small boulders
        ("BoulderGenerator", {
            "density": 0.04,
            "scale": 0.25,
            "spacing": 3,
            "boulder_type": "small"
        }),
        # Dead bushes
        ("DeadBushGenerator", {
            "density": 0.05,
            "scale": 0.3,
            "spacing": 3
        }),
    ],
    
    "swamp": [
        # Dead trees (no leaves)
        ("TreeGenerator", {
            "density": 0.06,
            "scale": 0.25,
            "spacing": 3,
            "tree_type": "dead"
        }),
        # Some living trees
        ("TreeGenerator", {
            "density": 0.02,
            "scale": 0.2,
            "spacing": 4,
            "tree_type": "standard"
        }),
        # Lots of mushrooms
        ("VegetationGenerator", {
            "density": 0.1,
            "scale": 0.35,
            "spacing": 2,
            "vegetation_type": "mushrooms"
        }),
        # Tall grass
        ("VegetationGenerator", {
            "density": 0.15,
            "scale": 0.4,
            "spacing": 2,
            "vegetation_type": "grass"
        }),
    ],
    
    "foothill": [
        # Mixed trees
        ("TreeGenerator", {
            "density": 0.04,
            "scale": 0.25,
            "spacing": 3,
            "tree_type": "standard"
        }),
        ("TreeGenerator", {
            "density": 0.02,
            "scale": 0.2,
            "spacing": 4,
            "tree_type": "pine"
        }),
        # Some boulders
        ("BoulderGenerator", {
            "density": 0.03,
            "scale": 0.22,
            "spacing": 4,
            "boulder_type": "small"
        }),
        # Grass
        ("VegetationGenerator", {
            "density": 0.12,
            "scale": 0.4,
            "spacing": 2,
            "vegetation_type": "grass"
        }),
    ],
    
    "beach": [
        # Very sparse - just some dead bushes
        ("DeadBushGenerator", {
            "density": 0.02,
            "scale": 0.25,
            "spacing": 4
        }),
    ],
    
    "river": [
        # Minimal structures (water feature)
        # Maybe add river stones in future
    ],
}


# STRUCTURE GENERATOR CLASS MAPPING
# Maps generator name strings to actual classes
# Used for dynamic instantiation from configuration

def get_structure_generators_for_biome(biome_name: str) -> list:
    """Get list of structure generators configured for a biome.
    
    Args:
        biome_name: Name of the biome
        
    Returns:
        List of (generator_class_name, config_dict) tuples
        
    Example:
        >>> generators = get_structure_generators_for_biome("forest")
        >>> for gen_name, config in generators:
        >>>     print(f"{gen_name}: density={config['density']}")
    """
    return BIOME_STRUCTURES.get(biome_name, [])


# USAGE NOTES:
#
# 1. Density guidelines:
#    - Very sparse: 0.01-0.03 (occasional features)
#    - Sparse: 0.03-0.06 (scattered)
#    - Moderate: 0.06-0.12 (noticeable presence)
#    - Dense: 0.12-0.25 (heavy coverage)
#
# 2. Scale guidelines:
#    - Large clusters: 0.1-0.2 (trees in groves, boulder fields)
#    - Medium distribution: 0.2-0.4 (natural spread)
#    - Scattered: 0.4-0.6 (individual placement, grass)
#
# 3. Spacing:
#    - Minimum blocks between structure spawn checks
#    - Lower = more CPU usage, more structures
#    - Higher = better performance, sparser placement
#    - Recommended: 2-5 blocks
#
# 4. Cross-chunk structures:
#    - Trees, logs, and rock formations can span chunks
#    - Generate from chunk data, not chunk boundaries
#    - Height callback handles cross-chunk terrain queries
