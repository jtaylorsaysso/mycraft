# Engine ↔ Game Boundaries

This document defines the clear separation between the **MyCraft Engine** and the **voxel_world Game**, establishing ownership, shared responsibilities, and out-of-scope features for each.

---

## Ownership Summary

| Domain | Owner | Examples |
|--------|-------|----------|
| Core Systems | Engine | ECS, Physics, Networking, Rendering |
| Game Logic | Game | Combat, PoI, Progression, Enemy AI |
| Tools & Editor | Engine | Visual map editor, asset pipeline |
| Content | Game | Biomes, blocks, entities, levels |
| Multiplayer Infra | Engine | Sync, discovery, connection handling |
| Gameplay Multiplayer | Game | Coop mechanics, shared objectives |

---

## Engine Responsibilities

### The engine provides

**Core Architecture**

- ECS framework (World, Entity, Component, System)
- Event bus for decoupled communication
- Configuration loading and game bootstrapping

**Physics & Movement**

- Kinematic character controller
- Collision detection and raycasting
- Gravity, slopes, water buoyancy
- *Generic* movement primitives (velocity, acceleration)

**Rendering**

- Panda3D integration and scene graph
- Mesh building and texture atlas
- Camera systems (orbital, first-person)
- Environment (skybox, lighting)

**Networking**

- Client/server architecture
- State synchronization
- LAN discovery
- Connection management

**Input**

- Input abstraction layer
- Keyboard/mouse/gamepad handling
- Input mapping system

**Tooling** *(Future)*

- Visual map editor
- Asset import/export
- In-game debugging tools

---

## Game Responsibilities

### voxel_world provides

**World Content**

- Biome definitions and parameters
- Block types and textures
- Terrain generation rules
- Points of Interest design

**Gameplay Systems**

- Combat system (attacks, timing, enemies)
- Traversal abilities (climb, vault, grab)
- PoI challenge mechanics
- Reward and progression systems

**Game-Specific Movement**

- Movement *feel* tuning (acceleration curves)
- Traversal abilities (game-specific verbs)
- Combat movement integration

**Entities & AI**

- Enemy types and behaviors
- Boss encounter design
- NPC interactions

**Player Experience**

- Spawn flow and tutorials
- HUD and game UI
- Audio and feedback
- Session flow (coop join/leave)

---

## Shared Boundaries

Some features span both layers with clear ownership:

| Feature | Engine Provides | Game Implements |
|---------|-----------------|-----------------|
| **Movement** | Physics primitives, collision | Traversal abilities, feel tuning |
| **Combat** | Damage/health components | Combat system, enemy AI |
| **Multiplayer** | Sync infrastructure | Coop mechanics, shared goals |
| **Camera** | Controller framework | Game-specific modes |
| **Terrain** | Chunk system, mesh building | Biome content, POI placement |
| **Input** | Abstraction layer | Action bindings, context |

### Decision Rule

> **If it's reusable across different games → Engine**
> **If it's specific to voxel_world's design → Game**

---

## Out of Scope

### Engine Will NOT Provide

| Feature | Reason |
|---------|--------|
| Combat mechanics | Game-specific design |
| Enemy AI behaviors | Content, not infrastructure |
| Quest/progression systems | Game design territory |
| Specific traversal abilities | Tied to game feel |
| PoI challenge design | Content |
| Game balancing | Game responsibility |
| Story/narrative systems | Content |

### Game Will NOT Implement

| Feature | Reason |
|---------|--------|
| Custom ECS framework | Use engine's World/System |
| Low-level networking | Use engine's sync layer |
| Custom rendering pipeline | Use engine's mesh/texture |
| Physics engine | Use engine's physics |
| Input handling at hardware level | Use engine's input abstraction |
| Tool development | Engine's domain |

---

## Feature Extraction Flow

When game features prove universally useful:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Game Prototype  →  Validate  →  Generalize  →    │
│                                                     │
│                   Extract to Engine                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Extraction Criteria:**

1. Feature is useful across multiple game types
2. Can be generalized without losing value
3. Doesn't embed game-specific assumptions
4. Has stable, tested API

**Examples of Extractable Features:**

- Generic climbing system → Engine physics extension
- Health/damage framework → Already engine component
- Waypoint/pathfinding → Engine AI utilities

**Examples That Stay in Game:**

- voxel_world's specific combat timing
- PoI challenge types
- Enemy behavior patterns
- Biome selection algorithms

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     voxel_world                         │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Biomes   │  │  Combat  │  │   PoIs   │  (Future)   │
│  │  Blocks   │  │  (TODO)  │  │  (TODO)  │             │
│  └───────────┘  └──────────┘  └──────────┘             │
├─────────────────────────────────────────────────────────┤
│                    MyCraft Engine                       │
│  ┌─────┐ ┌─────────┐ ┌───────────┐ ┌──────────┐        │
│  │ ECS │ │ Physics │ │ Rendering │ │ Network  │        │
│  └─────┘ └─────────┘ └───────────┘ └──────────┘        │
│  ┌─────────────────┐ ┌──────────────────────┐          │
│  │ PlayerControl   │ │ Water/Terrain/Spawn  │          │
│  └─────────────────┘ └──────────────────────┘          │
├─────────────────────────────────────────────────────────┤
│                      Panda3D                            │
└─────────────────────────────────────────────────────────┘
```

---

## Dependency Direction

```
Game → Engine → Panda3D
```

- **Game depends on Engine**: Never the reverse
- **Engine depends on Panda3D**: For rendering/scene
- **No circular dependencies**: Clean layer separation

### Import Rules

```python
# ✅ CORRECT: Game imports from engine
from engine.ecs.world import World
from engine.physics import PhysicsConstants

# ❌ WRONG: Engine imports from game
from games.voxel_world.biomes import BiomeRegistry  # NO!
```

### Registration Pattern

Games register their systems with the engine using hooks:

```python
# Game code (games/voxel_world/main.py)
from engine.game import VoxelGame
from games.voxel_world.systems.world_gen import TerrainSystem

# Create game instance
game = VoxelGame(name="My Game")

# Register game-specific terrain system
terrain_system = TerrainSystem(
    game.world, 
    game.world.event_bus, 
    game, 
    game.texture_atlas
)
game.register_terrain_system(terrain_system)
```

This maintains clean dependency direction: **Game → Engine → Panda3D**

---

## Decision Examples

| Question | Answer | Reasoning |
|----------|--------|-----------|
| "Where does climbing go?" | Game | Tied to voxel_world's traversal feel |
| "Where does gravity go?" | Engine | Universal physics constant |
| "Where do biomes go?" | Game | Content specific to voxel_world |
| "Where does mesh building go?" | Engine | Reusable rendering utility |
| "Where do enemies go?" | Game | Game-specific content |
| "Where does damage calculation go?" | Split | Engine: DamageSystem; Game: damage values |

---

*Last Updated: 2025-12-23*  
*Version: 1.0*
