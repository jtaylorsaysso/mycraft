"""Shrine structure generators for POI system.

Defines the structure generators for the 5 types of Challenge Shrines.
These generators create the physical block layout of the shrines.
"""

from typing import Optional, Callable, List, Tuple
from games.voxel_world.structures.structure_generator import StructureGenerator, Structure
import random

class PlainsAltarGenerator(StructureGenerator):
    """Generates a Plains Altar POI.
    
    Structure: A tall central stone pillar surrounded by smaller broken pillars.
    Designed to be visible from a distance in flat terrain.
    """
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        if not self.validate_placement(x, y, z, height_callback, min_flat_radius=3):
            return None
            
        blocks = []
        
        # Central Pillar (3x3 base, tapering to 1x1, 10-15 blocks tall)
        height = random.randint(10, 15)
        
        # Base/Podium
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                blocks.append((x + dx, y, z + dz, "stone_mossy"))
                
        # Main shaft
        for dy in range(height):
            # 3x3 core
            if dy < 4:
                for dx in range(-1, 2):
                    for dz in range(-1, 2):
                        blocks.append((x + dx, y + dy + 1, z + dz, "stone"))
            # 1x1 top
            else:
                blocks.append((x, y + dy + 1, z, "stone"))
                
        # Top Beacon/Light (Placeholder block)
        blocks.append((x, y + height + 1, z, "gold_block")) # Need to add gold block or similar
        
        # Surrounding small pillars
        for angle in [0, 90, 180, 270]:
            # Simple math for 4 corners at radius 4
            px, pz = 0, 0
            if angle == 0: px, pz = 4, 0
            elif angle == 90: px, pz = 0, 4
            elif angle == 180: px, pz = -4, 0
            elif angle == 270: px, pz = 0, -4
            
            p_height = random.randint(2, 4)
            for dy in range(p_height):
                blocks.append((x + px, y + dy, z + pz, "stone_mossy"))

        return Structure(blocks=blocks, origin=(x, y, z))


class ForestClearingGenerator(StructureGenerator):
    """Generates a Forest Clearing Shrine.
    
    Structure: A ring of mossy stones with a central pedestal.
    Clears trees in a radius (handled by placement logic ideally, but here just structural).
    """

    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        if not self.validate_placement(x, y, z, height_callback, min_flat_radius=4):
            return None
            
        blocks = []
        radius = 5
        
        # Stone circle
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                dist = (dx*dx + dz*dz)**0.5
                if 4.0 <= dist <= 5.5:
                    # Ring stones
                    if random.random() < 0.8: # Gaps in the ring
                        blocks.append((x + dx, y + 1, z + dz, "stone_mossy"))
                        if random.random() < 0.3: # Some taller
                             blocks.append((x + dx, y + 2, z + dz, "stone_mossy"))
        
        # Floor (cracked stone mix)
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                if dx*dx + dz*dz <= 9:
                    blocks.append((x + dx, y, z + dz, "cobblestone_mossy"))

        # Central Pedestal
        blocks.append((x, y + 1, z, "stone"))
        blocks.append((x, y + 2, z, "stone_mossy"))
        
        return Structure(blocks=blocks, origin=(x, y, z))


class MountainPeakGenerator(StructureGenerator):
    """Generates a Mountain Peak Shrine.
    
    Structure: An exposed stone platform at high altitude.
    """
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        # Needs validation but mountains are rugged. 
        # We might build a platform supported from below if needed.
        blocks = []
        
        # Platform 5x5
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                # Floor
                blocks.append((x + dx, y, z + dz, "stone"))
                # Support pillar down (in case of overhang)
                # Just go down 3 blocks for visual support
                for ddy in range(1, 4):
                     blocks.append((x + dx, y - ddy, z + dz, "cobblestone_mossy"))
        
        # Archway
        # Columns
        for dy in range(4):
            blocks.append((x - 2, y + dy + 1, z - 2, "ice"))
            blocks.append((x + 2, y + dy + 1, z - 2, "ice"))
            blocks.append((x - 2, y + dy + 1, z + 2, "ice"))
            blocks.append((x + 2, y + dy + 1, z + 2, "ice"))
            
        # Roof/Lintels
        for dx in range(-2, 3):
            blocks.append((x + dx, y + 5, z - 2, "stone"))
            blocks.append((x + dx, y + 5, z + 2, "stone"))
            
        return Structure(blocks=blocks, origin=(x, y, z))


class CanyonOutcropGenerator(StructureGenerator):
    """Generates a Canyon Outcrop Shrine.
    
    Structure: Suspended wooden platform or ruin on cliff edge.
    """
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        blocks = []
        
        # Wooden Platform
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                blocks.append((x + dx, y, z + dz, "wood"))
                
        # Fence/Railing (leaves/wood mix)
        for dx in range(-3, 4):
            blocks.append((x + dx, y + 1, z - 3, "wood"))
            blocks.append((x + dx, y + 1, z + 3, "wood"))
        for dz in range(-2, 3):
            blocks.append((x - 3, y + 1, z + dz, "wood"))
            blocks.append((x + 3, y + 1, z + dz, "wood"))
            
        # Central Totem
        for dy in range(1, 6):
            blocks.append((x, y + dy, z, "terracotta"))
            
        return Structure(blocks=blocks, origin=(x, y, z))


class RiversideRuinsGenerator(StructureGenerator):
    """Generates Riverside Ruins.
    
    Structure: Partially flooded stone walls.
    """
    
    def generate_structure(
        self,
        x: int,
        y: int,
        z: int,
        height_callback: Callable[[float, float], int]
    ) -> Optional[Structure]:
        blocks = []
        
        # Layout: L-shape wall ruin
        
        # Wall 1 (along X)
        for dx in range(-4, 5):
            h = random.randint(1, 4)
            for dy in range(h):
                blocks.append((x + dx, y + dy, z - 3, "stone_mossy"))
                
        # Wall 2 (along Z)
        for dz in range(-4, 5):
            h = random.randint(1, 4)
            for dy in range(h):
                blocks.append((x - 4, y + dy, z + dz, "stone_mossy"))
                
        # Debris pile
        for _ in range(10):
            dx = random.randint(-2, 2)
            dz = random.randint(-2, 2)
            blocks.append((x + dx, y + 1, z + dz, "cobblestone_mossy"))
            
        # Chest pedestal
        blocks.append((x + 2, y + 1, z + 2, "stone"))
        
        return Structure(blocks=blocks, origin=(x, y, z))
