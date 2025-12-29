"""Animation system for voxel characters."""

from engine.animation.core import (
    Transform,
    Keyframe,
    AnimationClip,
    VoxelRig,
    VoxelAnimator,
    ProceduralAnimator
)

from engine.animation.skeleton import (
    Bone,
    Skeleton,
    HumanoidSkeleton,
    BoneConstraints
)

from engine.animation.layers import (
    BoneMask,
    AnimationLayer,
    LayeredAnimator,
    AnimationSource
)

from engine.animation.sources import (
    ProceduralAnimationSource,
    KeyframeAnimationSource
)

from engine.animation.root_motion import (
    RootMotionCurve,
    RootMotionClip,
    RootMotionApplicator,
    add_root_motion_to_attack
)

from engine.animation.ik import (
    IKTarget,
    FABRIKSolver,
    IKLayer
)

from engine.animation.foot_ik import (
    FootIKController
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
    # Skeleton
    'Bone',
    'Skeleton',
    'HumanoidSkeleton',
    'BoneConstraints',
    # Layers
    'BoneMask',
    'AnimationLayer',
    'LayeredAnimator',
    'AnimationSource',
    # Sources
    'ProceduralAnimationSource',
    'KeyframeAnimationSource',
    # Root Motion
    'RootMotionCurve',
    'RootMotionClip',
    'RootMotionApplicator',
    'add_root_motion_to_attack',
    # IK
    'IKTarget',
    'FABRIKSolver',
    'IKLayer',
    'FootIKController',
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

