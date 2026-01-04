# MyCraft Engine Architecture

## For Beginners

**Don't worry about this document if you're just getting started!**

MyCraft's engine is designed so you can create games without understanding all these technical details. The complexity described here powers the visual tools and features you'll use, but it stays out of your way.

Think of it like driving a car - you don't need to know how the engine works to drive. But if you're curious or want to build your own custom features, this document explains what's under the hood.

---

## Overview

The MyCraft engine is designed as a reusable core separating generic game systems from specific game implementations. It relies heavily on an Entity Component System (ECS) architecture and is built on Panda3D.

## Structure

```text
engine/
├── animation/    # Hybrid procedural + keyframe animation system
│   ├── core.py           # Transform, Keyframe, AnimationClip, AnimationEvent
│   ├── layers.py         # LayeredAnimator, BoneMask, animation compositing
│   ├── skeleton.py       # HumanoidSkeleton (17-bone bipedal rig)
│   ├── mannequin.py      # VoxelAvatar visual rendering
│   ├── foot_ik.py        # Terrain-aware foot placement
│   ├── combat.py         # Combat animation clips (attacks, dodges, parries)
│   ├── root_motion.py    # Physics-driven attack movement
│   └── animation_registry.py  # Clip management + JSON I/O
├── core/         # Core utilities (logging, config, time)
├── ecs/          # The Entity Component System
├── input/        # Input management (InputManager, keybindings, action system)
├── player_mechanics/ # Player control mechanics (composable behaviors)
├── networking/   # Client/Server state synchronization + remote players
├── physics/      # Kinematic physics and collision
├── rendering/    # Rendering utilities (camera, texture atlas, environment)
├── systems/      # Core ECS systems (input, interaction, lifecycle, network, water)
└── ui/           # HUD and editor UI (OnscreenText, DirectGUI tools)
```

## Core Patterns

### Entity Component System (ECS)

- **World**: The container for all entities and systems.
- **Entity**: A unique ID with a collection of components.
- **Component**: Pure data containers (e.g., `Transform`, `Health`, `Inventory`).
- **System**: Logic that iterates over entities with specific components (e.g., `PlayerControlSystem` operates on `Transform` + physics state).

### Networking

The engine provides a `GameServer` and `GameClient` that handle:

- **State Snapshotting**: Server broadcasts world state at fixed intervals.
- **Input Handling**: ECS-based input systems (`PlayerControlSystem`, `GameplayInputSystem`).
- **Remote Players**: Panda3D NodePath-based rendering with interpolation.

### Physics

Kinematic physics engine focusing on:

- AABB Collision detection
- Raycasting (ground checks, wall checks)
- Gravity and friction simulation
- Water physics (buoyancy, drag, swimming)

### Player Mechanics

Priority-based mechanic system for player control:

- **Mechanic Pattern**: Composable, priority-ordered behaviors
- **PlayerContext**: Shared state container (input, transform, camera mode)
- **Built-in Mechanics**: Input polling, camera control, ground movement, animation
- **Coordinator**: `PlayerControlSystem` manages mechanic lifecycle and update order

See [Player Mechanics Documentation](player_mechanics.md) for details.

### Input Management

Action-based input abstraction:

- **InputManager**: Central polling system with mouse delta calculation
- **InputAction Enum**: Abstract actions (MOVE_FORWARD, CAMERA_TOGGLE_MODE, etc.)
- **InputMechanic**: High-priority mechanic (priority=1000) that populates PlayerContext
- **Keybindings**: Configurable key-to-action mapping

### Animation System

Hybrid procedural + keyframe animation for voxel characters:

- **Layered Composition**: Multiple animation sources combined with bone masking
- **Procedural Animations**: Runtime-generated walk/idle cycles
- **Keyframe Animations**: Combat attacks, dodges, parries with timing events
- **IK System**: FootIKController for terrain-aware foot placement
- **Root Motion**: Attack lunges driven by animation curves
- **Events**: Frame-perfect callbacks for combat hit windows

See [Animation System Documentation](ANIMATION_SYSTEM.md) for details.

### Rendering

Panda3D-based rendering with:

- **Camera**: Mode-based system (FirstPersonCamera, ExplorationCamera, CombatCamera) with smoothing, collision detection, auto-centering, and zoom. V-key toggle between modes.
- **Animation**: VoxelAvatar with LayeredAnimator for compositing locomotion, combat, and IK layers
- **Texture Atlas**: 16x16 tile grid system
- **Environment**: Lighting and atmosphere management
- **HUD**: OnscreenText-based UI
- **Editor UI**: DirectGUI-based tools (AnimationEditor with timeline visualization)

## Integration

Games are built by:

1. Defining game-specific Components and Systems in `games/<game_name>/`.
2. Registering these systems with the engine's `World` via `VoxelGame`.
3. Running the game through `run_client.py` or `launcher.py`.
