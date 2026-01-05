"""
Entity Factory for Voxel World.

Handles creation of game entities like enemies, loot, and projectiles,
centralizing component assembly and configuration.
"""

from typing import Tuple, Optional
from panda3d.core import LVector3f

from engine.components.core import Transform, Health, CombatState, Name, InputState
from engine.physics import KinematicState
from engine.components.avatar_colors import AvatarColors
from engine.components.enemy import EnemyComponent
from engine.color.palette import ColorPalette


class EntityFactory:
    """Factory for creating game entities."""
    
    @staticmethod
    def create_enemy(world, enemy_type: str, position: Tuple[float, float, float], seed: int, color_name: Optional[str] = None) -> str:
        """
        Create an enemy entity.
        
        Args:
            world: ECS World
            enemy_type: Type string ("skeleton", "zombie")
            position: (x, y, z) tuple
            seed: Random seed for variations/colors
            
        Returns:
            Entity ID
        """
        import random
        rng = random.Random(seed)
        
        entity = world.create_entity()
        
        # Core components
        world.add_component(entity, Transform(position=LVector3f(*position)))
        world.add_component(entity, Name(name=f"{enemy_type.capitalize()}"))
        
        # Physics (Kinematic character)
        world.add_component(entity, KinematicState())
        
        # Combat components
        world.add_component(entity, InputState()) # Required for combat system to read "inputs" (AI driven later)
        
        # 1. Base Stats & AI
        if enemy_type == "skeleton":
            # Fast, lower health
            world.add_component(entity, Health(current=50, max_hp=50))
            world.add_component(entity, CombatState(
                attack_damage=20.0,
                attack_range=2.0
            ))
            base_color = (0.9, 0.9, 0.85, 1.0) # Bone white
            
        elif enemy_type == "zombie":
            # Slow, high health
            world.add_component(entity, Health(current=80, max_hp=80))
            world.add_component(entity, CombatState(
                attack_damage=15.0,
                attack_range=1.5
            ))
            base_color = (0.4, 0.5, 0.4, 1.0) # Decay green
            
        else:
            # Fallback
            world.add_component(entity, Health(current=30, max_hp=30))
            world.add_component(entity, CombatState())
            base_color = (1.0, 1.0, 1.0, 1.0)

        # 2. Color System Integration
        
        # If color_name not provided, pick random from loot palette
        if not color_name:
            loot_color = ColorPalette.get_random_loot_color(rng)
            color_name = loot_color.name
        else:
            loot_color = ColorPalette.get_color(color_name)
            # Fallback if invalid name
            if not loot_color:
                loot_color = ColorPalette.STARTER_COLORS["red"]
                color_name = "red"
        
        # Add Enemy Component
        world.add_component(entity, EnemyComponent(
            enemy_type=enemy_type,
            tint_color=color_name,
            aggro_range=12.0 if enemy_type == "skeleton" else 10.0
        ))

        # Blend base color with loot color for "Tinting"
        # Skeleton: 40% tint
        # Zombie: 60% tint
        tint_strength = 0.6 if enemy_type == "zombie" else 0.4
        
        final_color = (
            base_color[0] * (1-tint_strength) + loot_color.rgba[0] * tint_strength,
            base_color[1] * (1-tint_strength) + loot_color.rgba[1] * tint_strength,
            base_color[2] * (1-tint_strength) + loot_color.rgba[2] * tint_strength,
            1.0
        )
        
        # We reuse AvatarColors component for visual sync
        # The EnemyVisual/AvatarColorSystem will read this
        avatar_colors = AvatarColors(
            body_color=final_color
        )
        world.add_component(entity, avatar_colors)
        
        # Add Loot Component
        from engine.components.loot import LootComponent
        world.add_component(entity, LootComponent(color_name=color_name))
        
        # Note: Visual representation is handled by AvatarColorSystem 
        # (for color) and AnimationSystem (for mesh) implicitly?
        # Actually, we need to ensure the VoxelAvatar is created.
        # Usually that happens in a visual system. 
        # For now, let's assume AnimationMechanic or similar handles players,
        # but for enemies, we might need to manually attach the visual 
        # OR rely on a system. The plan mentioned EnemyVisual class.
        
        return entity
