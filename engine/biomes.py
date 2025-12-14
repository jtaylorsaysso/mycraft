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
        and variety across the world.
        
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
        
        # Map noise value to biomes
        # Value range is roughly -2 to +2
        if biome_value < -1.0:
            return cls.get_biome("desert")
        elif biome_value < 0.0:
            return cls.get_biome("rocky")
        elif biome_value < 1.0:
            return cls.get_biome("plains")
        else:
            return cls.get_biome("forest")


# Height generation functions for each biome

def plains_height(x: float, z: float) -> int:
    """Baseline terrain: gentle rolling hills.
    
    Action-RPG oriented:
    - Ground level at y=0
    - Gentle slopes (±2 blocks)
    - Clear paths and readable combat spaces
    """
    base_height = 0
    
    # Gentle sine waves for broad, readable terrain
    wave_x = math.sin(x * 0.05) * 2
    wave_z = math.cos(z * 0.05) * 2
    
    height = base_height + wave_x + wave_z
    height = max(-2, min(2, height))
    
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
    - Larger amplitude (±4 blocks)
    - Plateaus and small cliffs
    - Still readable for combat
    """
    base_height = 0
    
    # Larger amplitude waves
    wave_x = math.sin(x * 0.04) * 3
    wave_z = math.cos(z * 0.03) * 3
    
    # Add some plateau effect
    plateau = math.floor(math.sin(x * 0.02) * 2) * 1.5
    
    height = base_height + wave_x + wave_z + plateau
    height = max(-4, min(4, height))
    
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
    subsurface_block="gravel"
))

BiomeRegistry.register(Biome(
    name="desert",
    display_name="Desert",
    height_function=desert_height,
    surface_block="sand",
    subsurface_block="sand"
))
