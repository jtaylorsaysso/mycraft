# Voxel World Game Documentation

## Overview

`voxel_world` is the flagship implementation using the MyCraft engine. It is a Minecraft-like voxel sandbox game.

## Key Systems

### World Generation (`systems/world_gen.py`)

- **Chunk-based**: World is divided into 16x16x256 chunks.
- **Procedural Generation**: Uses noise functions to generate terrain.
- **Biome**: 8 distinct biomes defined in `biomes/` (Plains, Forest, Rocky, Desert, Mountain, Canyon, River, Beach, Swamp).

### Entities

#### Player

- **Local Player**: Controlled by the user, predicts own movement.
- **Remote Player**: Interpolated representation of other connected users.
- **Mannequin**: 5-part hierarchical model for character animation.

### Water Physics (`engine/systems/water_physics.py`)

- **Buoyancy**: Entities float in water based on submersion level.
- **Swimming**: Resistance and vertical movement when submerged.

### Blocks

Block types are registered in `blocks/registry.py`:

- Grass, Dirt, Stone, Bedrock, etc.
- Each block defines texture coordinates for the Texture Atlas.

## Directory Structure

```text
games/voxel_world/
├── biomes/       # Biome definitions
├── blocks/       # Block registry and data
├── components/   # Game-specific components (e.g., Inventory)
├── entities/     # Prefabs for players/mobs
├── systems/      # Game logic systems
├── ui/           # HUD and Menu implementations
├── main.py       # Game entry point
└── config/       # Default game configuration
```
