# voxel_world - The Flagship Game

**voxel_world** is the flagship game built with MyCraft - an exploration-driven action adventure focused on deep movement mechanics and momentum-based combat.

### For Players

voxel_world offers a cooperative adventure where you:

- **Explore** a vast, vertical world marked by mysterious ruins
- **Master** deep traversal mechanics: climbing, vaulting, and sliding
- **Battle** enemies using timing, positioning, and momentum
- **Discover** hidden Points of Interest and overcome their challenges

### For Creators

voxel_world demonstrates the engine's capabilities:

- **Example**: Shows how to build a complete game on MyCraft
- **Template**: Provides a solid foundation for action games
- **Proving Ground**: The place where new engine features are tested

---

## Key Features

### World & Biomes

**8 Distinct Biomes:**

- **Plains**: Rolling hills for mastering movement speed
- **Forest**: Dense vegetation with vertical opportunities
- **Rocky**: Cliffs and plateaus for climbing challenges
- **Desert**: Open dunes for sliding and momentum
- **Mountain**: Epic peaks requiring advanced traversal
- **Canyon**: Technical jumps and wall interactions
- **River**: Fast travel channels
- **Beach** & **Swamp**: Transitions and unique terrain

### Gameplay Loop

**Explore → Discover → Challenge → Reward**

1. **Spot** a Point of Interest on the horizon
2. **Traverse** the terrain using parkour skills
3. **Overcome** the combat or puzzle challenge
4. **Collect** the reward and find the next landmark

### Multiplayer

- **Cooperative PvE**: Adventure together with no friendly fire
- **Shared Discovery**: Spot landmarks for your team
- **Tactical Combat**: Flank enemies while allies distract

---

## Game Structure

### Directory Layout

```
games/voxel_world/
├── biomes/           # Procedural terrain generation
├── blocks/           # Content definitions
├── systems/          # Game-specific logic (Combat, AI)
├── config/           # Game balancing
└── main.py           # Entry point
```

---

## Development Status

### Completed ✅

- 8 biomes with Perlin noise terrain
- Basic physics and collision
- Multiplayer networking

### In Progress 🚧

- **Movement**: Climbing, vaulting, and fluid traversal
- **Combat**: Basic attacks and enemy interactions
- **Content**: First Challenge Shrine prototype

### Planned 📋

- **Advanced Movement**: Wall mechanics, gliding
- **Combat System**:
  - Momentum-based damage (velocity increases power)
  - Stamina management for dodge and parry
  - Skeleton enemy with telegraph-based AI
  - See [COMBAT_SYSTEM.md](../../docs/design/COMBAT_SYSTEM.md) for details
- **Points of Interest**: Procedural ruins and camps
- **Progression**: Unlockable abilities

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
