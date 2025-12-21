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
├── animation/    # Panda3D-based procedural animation system
├── core/         # Core utilities (logging, config, time)
├── ecs/          # The Entity Component System
├── input/        # Input management (keyboard, mouse)
├── networking/   # Client/Server state synchronization + remote players
├── physics/      # Kinematic physics and collision
├── rendering/    # Rendering utilities (camera, texture atlas, environment)
├── systems/      # Core ECS systems (input, interaction, lifecycle, network, water)
└── ui/           # HUD and UI components (OnscreenText-based)
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

### Rendering

Panda3D-based rendering with:

- **Camera**: FPS camera with smoothing and collision
- **Texture Atlas**: 16x16 tile grid system
- **Environment**: Lighting and atmosphere management
- **HUD**: OnscreenText-based UI

## Integration

Games are built by:

1. Defining game-specific Components and Systems in `games/<game_name>/`.
2. Registering these systems with the engine's `World` via `VoxelGame`.
3. Running the game through `run_client.py` or `launcher.py`.
