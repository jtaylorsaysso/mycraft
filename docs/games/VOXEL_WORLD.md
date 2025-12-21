# voxel_world - The Flagship Game

## What is voxel_world?

**voxel_world** is the first game built with MyCraft - a Minecraft-inspired action-RPG adventure. It's both a playable game and a demonstration of what you can create with the MyCraft engine.

### For Playtesters

voxel_world is your playground to:

- **Explore** 8 unique biomes with varied terrain
- **Adventure** with friends in multiplayer
- **Discover** the possibilities of voxel worlds

See the [Player Guide](../../PLAYER_GUIDE.md) for controls and gameplay.

### For Creators

voxel_world serves as:

- **Example**: See what's possible with MyCraft
- **Template**: Use it as a starting point for your own game
- **Inspiration**: Learn from how it's built

---

## Key Features

### World & Biomes

**8 Distinct Biomes:**

- **Plains**: Gentle rolling hills, perfect for building
- **Forest**: Dense vegetation with varied elevation
- **Rocky**: Dramatic cliffs and plateaus
- **Desert**: Flat sandy expanses
- **Mountain**: Towering peaks and valleys
- **Canyon**: Deep gorges with mesa tops
- **River**: Flowing water channels
- **Beach**: Coastal transitions
- **Swamp**: Low-lying wetlands

Each biome has unique terrain generation, block types, and visual character.

### Multiplayer

- **LAN-based**: Play with friends on your local network
- **Real-time sync**: See other players move in real-time
- **Zero-config**: Auto-discovery on WiFi
- **Admin console**: In-game server management

See the [Networking Guide](../networking_guide.md) for technical details.

### Physics & Movement

- **Smooth movement**: Acceleration-based controls
- **Mario-style jumping**: Variable height, coyote time, jump buffering
- **Slope handling**: Walk up gentle slopes, slide down steep ones
- **Water physics**: Buoyancy and swimming mechanics

See the [Physics System](../physics_system.md) for implementation details.

---

## Game Structure

### Directory Layout

```
games/voxel_world/
├── biomes/           # Biome definitions and terrain generation
│   ├── biomes.py     # BiomeRegistry and biome classes
│   └── noise.py      # Perlin noise utilities
├── blocks/           # Block types and properties
│   └── blocks.py     # BlockRegistry
├── systems/          # Game-specific ECS systems
│   ├── world_gen.py  # TerrainSystem for chunk generation
│   └── gameplay_input.py  # GameplayInputSystem
├── config/           # Game configuration
└── main.py           # Game entry point
```

### How It Works

1. **Terrain Generation**: `TerrainSystem` creates chunks using biome-specific height functions
2. **Player Control**: `PlayerControlSystem` handles movement and physics
3. **Gameplay Input**: `GameplayInputSystem` manages game-specific actions
4. **Networking**: `SyncSystem` synchronizes state across clients

---

## For Creators: Customizing voxel_world

### Easy Customizations

**Change Textures:**

- Edit `terrain.png` in the root directory
- Modify block texture coordinates in `blocks/blocks.py`

**Adjust Biomes:**

- Edit height functions in `biomes/biomes.py`
- Change block types for surface/subsurface

**Tune Physics:**

- Modify constants in `engine/physics/constants.py`
- Adjust player speed, jump height, gravity

### Advanced Customizations

**Add New Biomes:**

1. Define biome class in `biomes/biomes.py`
2. Create height function
3. Register with `BiomeRegistry`
4. Update biome selection logic

**Add New Blocks:**

1. Register in `blocks/blocks.py`
2. Define texture coordinates
3. Use in biome definitions

**Custom Systems:**

1. Create new system class in `systems/`
2. Register with `World` in `main.py`
3. Implement `update()` logic

---

## Development Status

### Completed ✅

- 8 biomes with Perlin noise terrain
- Multiplayer networking
- Physics and movement
- Water physics
- Character animation

### In Progress 🚧

- Content expansion (more blocks, items)
- Gameplay loop (progression, objectives)
- Polish and optimization

### Planned 📋

- Combat system
- Inventory and crafting
- NPC entities
- Quests and story

---

## Technical Details

### Engine Systems Used

voxel_world demonstrates these MyCraft engine features:

- **ECS Architecture**: World, entities, components, systems
- **Physics**: Kinematic movement, collision detection
- **Networking**: Client/server architecture, state sync
- **Rendering**: Mesh generation, texture atlas, camera
- **Animation**: Procedural character animations

### Performance

- **Chunk size**: 16×16 blocks
- **Render distance**: Configurable (default 3 chunks)
- **Target FPS**: 60
- **Network tick**: 20Hz server, 10Hz client

---

## Contributing

Want to improve voxel_world?

- **Report bugs**: Open issues on GitHub
- **Suggest features**: Share your ideas
- **Create content**: Design biomes, blocks, textures
- **Write code**: Submit pull requests

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines *(Coming Soon)*.

---

*Last Updated: 2025-12-20*  
*Version: 2.0 - Beginner-Friendly*
