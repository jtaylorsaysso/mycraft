# MyCraft Engine Architecture

## Overview

The MyCraft engine is designed as a reusable core separating generic game systems from specific game implementations. It relies heavily on an Entity Component System (ECS) architecture.

## Structure

```text
engine/
├── core/         # Core utilities (logging, config, time)
├── ecs/          # The Entity Component System
├── networking/   # Client/Server state synchronization
├── physics/      # Kinematic physics and collision
└── rendering/    # Abstraction layer for rendering (Ursina)
```

## Core Patterns

### Entity Component System (ECS)

- **World**: The container for all entities and systems.
- **Entity**: A unique ID with a collection of components.
- **Component**: Pure data containers (e.g., `Transform`, `Velocity`, `Mesh`).
- **System**: Logic that iterates over entities with specific components (e.g., `MovementSystem` operates on `Transform` + `Velocity`).

### Networking

The engine provides a `GameServer` and `GameClient` that handle:

- **State Snapshotting**: Server broadcasts world state at fixed intervals.
- **Input Prediction**: Clients predict local movement.
- **Reconciliation**: Clients smooth out remote entity movement.

### Physics

Kinematic physics engine focusing on:

- AABB Collision detection
- Raycasting
- Gravity and friction simulation

## Integration

Games are built by:

1. Defining game-specific Components and Systems in `games/<game_name>/`.
2. Registering these systems with the engine's `World`.
3. Running the `GameApp` with the configured World.
