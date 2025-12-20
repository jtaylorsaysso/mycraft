"""Animation system for voxel characters."""

from engine.animation.core import (
    Transform,
    Keyframe,
    AnimationClip,
    VoxelRig,
    VoxelAnimator,
    ProceduralAnimator
)

from engine.animation.combat import (
    HitWindow,
    CombatClip,
    CombatAnimator,
    create_walk_cycle,
    create_sword_slash
)

from engine.animation.particles import (
    VoxelParticle,
    VoxelParticleSystem,
    create_impact_effect,
    create_dust_cloud
)

__all__ = [
    # Core
    'Transform',
    'Keyframe',
    'AnimationClip',
    'VoxelRig',
    'VoxelAnimator',
    'ProceduralAnimator',
    # Combat
    'HitWindow',
    'CombatClip',
    'CombatAnimator',
    'create_walk_cycle',
    'create_sword_slash',
    # Particles
    'VoxelParticle',
    'VoxelParticleSystem',
    'create_impact_effect',
    'create_dust_cloud',
]
