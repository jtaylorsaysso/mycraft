# MyCraft Entity Sizing Standards

## Overview

This document defines the standardized sizing conventions for entities in MyCraft to ensure consistency across the codebase and alignment with voxel engine best practices.

## Core Standards

### Block Scale

- **Scale**: `1.0` (unit cube)
- **Rationale**: Maintains 1:1 unit-to-block ratio for intuitive calculations
- **Usage**: All world blocks, terrain, and building materials

### Player Scale

- **Total Height**: `1.8` units
- **Rationale**: Matches industry standard (Minecraft) where 1 block = 1 meter and player = 1.8m
- **Body Proportions**:
  - Head: `0.3` units height, positioned at `y=1.6`
  - Torso: `1.2` units height, positioned at `y=0.9`
  - Legs: `1.0` units height, positioned at `y=0.3`
- **Width/Depth**: `0.3` units for head, `0.4` units for torso/legs

## Coordinate System

### World Coordinates

- **Origin**: `(0, 0, 0)` at world center
- **Block Positioning**: Integer coordinates for block placement
- **Ground Level**: `y=1` for first block layer

### Entity Positioning

- **Player Spawn**: `(0, 2, 0)` - 1 block above ground
- **Camera**: Third-person over-the-shoulder at `(0, 5, -10)` relative to player

## Chunk Standards (Planned)

### Chunk Dimensions

- **Size**: `16×16×16` blocks
- **Rationale**: Industry standard balancing render performance and rebuild times
- **World Units**: Each chunk occupies `16×16×16` world units

### Performance Considerations

- **Render Calls**: 1 call per chunk vs 1 call per block
- **Trade-off**: Larger chunks = fewer renders but slower rebuilds on modification
- **Boundary Updates**: Chunks sharing modified boundaries require rebuilds

## Implementation Guidelines

### Adding New Entities

1. Use block scale (`1.0`) as base reference
2. Position player entities relative to 1.8 unit height standard
3. Maintain integer positioning for world blocks
4. Use consistent color schemes: `color.rgb(150, 125, 100)` for player body parts

### Camera Setup

- Third-person camera should maintain `position = (0, 5, -10)` relative to player
- Use camera pivot entity for smooth rotation
- Camera should always look at player center

## Current Implementation Status

### ✅ Implemented

- **Block Scale**: 1.0 unit cubes with integer positioning
- **Player Scale**: 1.8 unit height with proportional body parts
- **Chunk System**: 16×16 blocks per chunk with optimized meshing
- **Camera**: Over-the-shoulder third-person with collision prevention
- **Physics Module**: Reusable kinematic physics with Mario-style jumping
- **Network Integration**: TCP-based LAN multiplayer with player synchronization

### 🔄 Active Design

- **Entity Sizing**: Following voxel engine standards for consistency
- **Performance**: Mesh optimization reducing draw calls significantly
- **Architecture**: Clean separation between player, world, camera, physics, and networking systems
- **Jump Feel**: Mario-style variable height, coyote time, and jump buffering
- **Multiplayer**: Real-time position sync with remote player representation

## Future Considerations

### Entity Variations

- Different player models should maintain 1.8 unit height
- Mob entities will be scaled relative to player height
- Block variations (slabs, stairs) will use fractions of unit scale

### World Generation

- Terrain height maps should use integer values
- Structures should align to block grid
- Biome transitions should maintain block boundaries

## References

### External Standards
- [Minecraft Wiki - Units of Measure](https://minecraft.fandom.com/wiki/Tutorials/Units_of_measure)
- [Ursina Engine Documentation](https://www.ursinaengine.org/)
- [Voxel Engine Best Practices](https://sites.google.com/site/letsmakeavoxelengine/)

### Internal Files
- `engine/player.py` - Player entity implementation
- `engine/world.py` - World generation and block placement
- `engine/game_app.py` - Main game application setup

---
*Last Updated: 2025-11-22*
*Version: 1.0*
