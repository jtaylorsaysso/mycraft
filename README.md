# MyCraft - Action-RPG Voxel Engine

A 3D action-RPG oriented voxel engine built with the Ursina engine, focusing on performance and clean architecture.

## Features

### Current Implementation

- **3D World**: Chunk-based terrain generation with action-RPG oriented design
  - 3×3 chunk grid (16×16 blocks per chunk)
  - Gentle rolling terrain with height variation
  - Optimized mesh rendering (greedy meshing for top faces)
  - Static terrain (no block destruction/placement baseline)
- **Player**: 1.8 unit height character with over-the-shoulder third-person camera
  - Camera collision prevention with raycasting
  - Smooth movement with gravity and jumping
- **Performance Optimizations**:
  - Per-chunk meshing (single mesh per chunk)
  - Greedy meshing for top surfaces
  - Side face culling based on height differences
  - Reduced draw calls from thousands to single digits

### Controls

- **W/A/S/D**: Movement (relative to camera direction)
- **Mouse**: Camera rotation (when locked) - rotates around player
- **Space**: Jump (with gravity)
- **Escape**: Release/toggle mouse cursor

## Architecture

```text
mycraft/
├── engine/           # Core game logic
│   ├── game_app.py   # Main game entry point
│   ├── player.py     # Player entity with input handling
│   ├── input_handler.py # Movement and camera controls
│   ├── world.py      # World generation
│   └── assets/       # Game assets
├── network/          # Multiplayer components (placeholder)
├── util/             # Utilities (placeholder)
├── run_client.py     # Launch game client
└── run_server.py     # Launch server (placeholder)
```

## Running the Game

```bash
# Activate virtual environment (if using one)
source .venv/bin/activate

# Run the game
python run_client.py
```

## Dependencies

- **Python 3.12+**
- **Ursina 8.2.0** (3D game engine)

## Development Status

This is a **performance-focused voxel engine foundation** with:

- Chunk-based world generation optimized for action-RPG gameplay
- Efficient mesh rendering system
- Clean separation between player, world, and input systems
- Documentation-driven development approach

Future planned features:
- Dynamic chunk loading/unloading
- Multi-layer terrain support
- Action-RPG gameplay mechanics
- Expanded world generation features

## Technical Notes

### World Generation

- **Chunk System**: 16×16 blocks per chunk, 3×3 chunk grid (48×48 total)
- **Height Function**: Gentle sine waves with y=0 ground baseline
- **Meshing**: Greedy meshing for top faces, side face culling
- **Performance**: Single mesh per chunk vs thousands of individual entities

### Player System

- **Entity Sizing**: 1.8 unit height following voxel engine standards
- **Camera**: Over-the-shoulder third-person with raycast collision prevention
- **Movement**: WASD with mouse look, gravity and jumping mechanics

### Architecture

- **Modular Design**: Clear separation between Player, World, InputHandler
- **Performance First**: Mesh optimization and chunk-based rendering
- **Documentation**: Entity sizing standards and world generation guidelines
