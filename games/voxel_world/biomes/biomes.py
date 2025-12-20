"""Biome definitions and registry for terrain variety.

This module defines biomes that control terrain generation characteristics.
Each biome has its own height generation function and block type mappings,
providing visual and structural variety while maintaining action-RPG oriented
playability (readable spaces, gentle slopes, clear navigation).
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional
import math


@dataclass
class Biome:
    """Represents a biome type with terrain generation parameters.
    
    Attributes:
        name: Internal identifier (lowercase, no spaces)
        display_name: Human-readable name
        height_function: Function(x, z) -> int that generates terrain height
        surface_block: Block type name for top surface
        subsurface_block: Block type name for blocks below surface
        color_tint: Optional RGB tuple to tint the biome's appearance
    """
    name: str
    display_name: str
    height_function: Callable[[float, float], int]
    surface_block: str
    subsurface_block: str
    color_tint: Optional[tuple[float, float, float]] = None


class BiomeRegistry:
    """Central registry for all biome types.
    
    Singleton pattern - use BiomeRegistry.register() and BiomeRegistry.get_biome()
    """
    
    _biomes: Dict[str, Biome] = {}
    
    @classmethod
    def register(cls, biome: Biome) -> None:
        """Register a new biome type.
        
        Args:
            biome: Biome instance to register
            
        Raises:
            ValueError: If biome name already registered
        """
        if biome.name in cls._biomes:
            raise ValueError(f"Biome '{biome.name}' already registered")
        cls._biomes[biome.name] = biome
    
    @classmethod
    def get_biome(cls, name: str) -> Biome:
        """Look up a biome by name.
        
        Args:
            name: Biome identifier
            
        Returns:
            Biome instance
            
        Raises:
            KeyError: If biome not found
        """
        if name not in cls._biomes:
            raise KeyError(f"Biome '{name}' not registered")
        return cls._biomes[name]
    
    @classmethod
    def exists(cls, name: str) -> bool:
        """Check if a biome is registered.
        
        Args:
            name: Biome identifier
            
        Returns:
            True if biome exists in registry
        """
        return name in cls._biomes
    
    @classmethod
    def get_all_biomes(cls) -> Dict[str, Biome]:
        """Get all registered biomes.
        
        Returns:
            Dictionary of biome name -> Biome instance
        """
        return cls._biomes.copy()
    
    @classmethod
    def get_biome_at(cls, x: float, z: float) -> Biome:
        """Determine which biome should be used at world coordinates (x, z).
        
        Uses simple noise-based biome selection for smooth transitions
        and variety across the world. Now includes mountain and canyon biomes.
        
        Args:
            x: World X coordinate
            z: World Z coordinate
            
        Returns:
            Biome instance for this location
        """
        # Simple biome noise using sine waves
        # Low frequency to create large biome regions
        biome_noise_x = math.sin(x * 0.01) * math.cos(z * 0.01)
        biome_noise_z = math.cos(x * 0.015) * math.sin(z * 0.015)
        biome_value = biome_noise_x + biome_noise_z
        
        # Secondary noise for more variety
        secondary_noise = math.sin(x * 0.008) * math.cos(z * 0.012)
        
        # Map noise value to biomes
        # Extended value range for new biomes
        # River noise (ridges: variables width)
        river_noise = abs(math.sin(x * 0.015 + z * 0.005) + math.cos(z * 0.012 - x * 0.005))
        if river_noise < 0.15: # Narrow bands
             return cls.get_biome("river")

        # Main biome selection
        if biome_value < -1.5:
            return cls.get_biome("canyon")  # Deep valleys
        elif biome_value < -0.8:
            # Check for water proximity for beach/swamp
            # Water noise (simulating moisture/water level)
            water_noise = math.sin(x * 0.02) * math.cos(z * 0.02)
            
            # If low terrain and high moisture/water proximity
            if secondary_noise < -0.2: 
                if water_noise > 0.0:
                    return cls.get_biome("swamp")
                else:
                    return cls.get_biome("beach")
            else:
                return cls.get_biome("desert")
        elif biome_value < 0.0:
            return cls.get_biome("rocky")
        elif biome_value < 0.8:
            return cls.get_biome("plains")
        elif biome_value < 1.5:
            return cls.get_biome("forest")
        else:
            # High values = mountains (use secondary noise for variety)
            if secondary_noise > 0:
                return cls.get_biome("mountain")
            else:
                return cls.get_biome("rocky")  # Rocky highlands near mountains


# Height generation functions for each biome

def plains_height(x: float, z: float) -> int:
    """Baseline terrain: gentle rolling hills.
    
    Action-RPG oriented:
    - Ground level at y=0
    - Gentle slopes (±3 blocks) - enhanced for movement variety
    - Clear paths and readable combat spaces
    """
    base_height = 0
    
    # Gentle sine waves for broad, readable terrain
    wave_x = math.sin(x * 0.05) * 2.5
    wave_z = math.cos(z * 0.05) * 2.5
    
    # Add subtle detail
    detail = math.sin(x * 0.1) * math.cos(z * 0.1) * 0.5
    
    height = base_height + wave_x + wave_z + detail
    height = max(-3, min(3, height))
    
    return int(round(height))


def forest_height(x: float, z: float) -> int:
    """Forest terrain: similar to plains but with tree-like features.
    
    Same height profile as plains, allowing block placement to
    create "tree" pillars in the chunk generation.
    """
    return plains_height(x, z)


def rocky_height(x: float, z: float) -> int:
    """Rocky terrain: more dramatic height variation.
    
    Features:
    - Larger amplitude (±6 blocks) - enhanced for climbing
    - Sharper plateaus and cliffs
    - Good for vertical movement practice
    """
    base_height = 0
    
    # Larger amplitude waves
    wave_x = math.sin(x * 0.04) * 3.5
    wave_z = math.cos(z * 0.03) * 3.5
    
    # Sharper plateau effect for cliff-like features
    plateau = math.floor(math.sin(x * 0.02) * 2.5) * 2
    
    # Add some roughness
    roughness = math.sin(x * 0.08) * math.cos(z * 0.08) * 0.8
    
    height = base_height + wave_x + wave_z + plateau + roughness
    height = max(-6, min(6, height))
    
    return int(round(height))


def desert_height(x: float, z: float) -> int:
    """Desert terrain: very flat with minimal variation.
    
    Features:
    - Almost completely flat (±1 block)
    - Occasional gentle dunes
    - Maximum visibility and movement
    """
    base_height = 0
    
    # Very gentle waves
    wave_x = math.sin(x * 0.03) * 0.5
    wave_z = math.cos(z * 0.03) * 0.5
    
    height = base_height + wave_x + wave_z
    height = max(-1, min(1, height))
    
    return int(round(height))


def mountain_height(x: float, z: float) -> int:
    """Mountain terrain: dramatic height variation for climbing challenges.
    
    Features:
    - Very large amplitude (±8 to ±12 blocks)
    - Sharp peaks and deep valleys
    - Plateau generation for "rest points"
    - Designed for vertical movement mechanics
    """
    base_height = 0
    
    # Large amplitude waves for dramatic terrain
    wave_x = math.sin(x * 0.03) * 6
    wave_z = math.cos(z * 0.025) * 6
    
    # Sharp peaks using squared sine
    peaks = (math.sin(x * 0.015) ** 2) * 3
    peaks += (math.cos(z * 0.015) ** 2) * 3
    
    # Plateau effect for flat "rest areas"
    plateau = math.floor(math.sin(x * 0.01) * 1.5) * 2
    
    height = base_height + wave_x + wave_z + peaks + plateau
    height = max(-8, min(12, height))
    
    return int(round(height))


def canyon_height(x: float, z: float) -> int:
    """Canyon/Mesa terrain: deep valleys with flat tops.
    
    Features:
    - Height range: -6 to +2 (deep canyons, low mesas)
    - Sharp drop-offs and flat mesa tops
    - Stepped terrain (parkour-friendly)
    - Good for horizontal jumping challenges
    """
    base_height = -2  # Biased toward valleys
    
    # Create mesa shapes with flat tops
    mesa_x = math.sin(x * 0.04) * 4
    mesa_z = math.cos(z * 0.04) * 4
    
    # Flatten the tops using floor function (creates sharp edges)
    mesa_top = math.floor((mesa_x + mesa_z) / 2)
    
    # Add stepped terrain for parkour
    steps = math.floor(math.sin(x * 0.08) * 1.5)
    
    # Sharp valley cuts
    valley = math.sin(x * 0.02) * math.cos(z * 0.02) * 3
    
    height = base_height + mesa_top + steps + valley
    height = max(-6, min(2, height))
    
    return int(round(height))


def river_height(x: float, z: float) -> int:
    """Riverbed terrain: carves a channel.
    
    Features:
    - Below water level (y=-2 to -4)
    - Smooth curved bottom
    """
    # Base depth
    base_depth = -3
    
    # Add some variation to river depth
    variation = math.sin(x * 0.1) * 0.5
    
    height = base_depth + variation
    
    return int(round(height))


def beach_height(x: float, z: float) -> int:
    """Beach terrain: flat, near water level.
    
    Features:
    - Very flat (y=-1 to 0)
    - Gentle slope towards water
    """
    base_height = -0.5
    
    # Very gentle slope
    wave = math.sin(x * 0.02) * 0.5 + math.cos(z * 0.02) * 0.5
    
    height = base_height + wave * 0.5
    height = max(-1, min(0, height))
    
    return int(round(height))


def swamp_height(x: float, z: float) -> int:
    """Swamp terrain: low lying with pools.
    
    Features:
    - Mostly at y=-1 or y=-2
    - Occasional mounds at y=0
    - Perfect for shallow water pools
    """
    base_height = -1
    
    # Mounds and pools
    mound = math.sin(x * 0.1) * math.cos(z * 0.1)
    
    height = base_height + mound
    height = max(-2, min(0, height))
    
    return int(round(height))


# Register default biomes

BiomeRegistry.register(Biome(
    name="plains",
    display_name="Plains",
    height_function=plains_height,
    surface_block="grass",
    subsurface_block="dirt"
))

BiomeRegistry.register(Biome(
    name="forest",
    display_name="Forest",
    height_function=forest_height,
    surface_block="wood",  # Tree-like appearance
    subsurface_block="dirt"
))

BiomeRegistry.register(Biome(
    name="rocky",
    display_name="Rocky Highlands",
    height_function=rocky_height,
    surface_block="stone",
    subsurface_block="cobblestone_mossy"  # Enhanced with mossy variation
))

BiomeRegistry.register(Biome(
    name="desert",
    display_name="Desert",
    height_function=desert_height,
    surface_block="sand",
    subsurface_block="sandstone"  # Enhanced with sandstone layer
))

BiomeRegistry.register(Biome(
    name="mountain",
    display_name="Mountain Peaks",
    height_function=mountain_height,
    surface_block="stone",  # Can be snow at high elevations (future enhancement)
    subsurface_block="stone"
))

BiomeRegistry.register(Biome(
    name="canyon",
    display_name="Canyon Mesa",
    height_function=canyon_height,
    surface_block="red_sand",
    subsurface_block="terracotta"  # Mesa-like layering
))


BiomeRegistry.register(Biome(
    name="beach",
    display_name="Sandy Beach",
    height_function=beach_height,
    surface_block="sand",
    subsurface_block="sandstone"
))

BiomeRegistry.register(Biome(
    name="swamp",
    display_name="Muddy Swamp",
    height_function=swamp_height,
    surface_block="mud",  # Needs mud block
    subsurface_block="dirt",
    color_tint=(0.4, 0.5, 0.3)  # Murky green tint (if supported)
))

BiomeRegistry.register(Biome(
    name="river",
    display_name="River",
    height_function=river_height,
    surface_block="sand",
    subsurface_block="gravel"
))
