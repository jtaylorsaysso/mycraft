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
- **Physics System**: Centralized kinematic controller with:
  - Mario-style jumping (variable height, coyote time, jump buffering)
  - Raycast-based ground detection against chunk meshes
  - Reusable physics module for future entities
- **LAN Multiplayer**: TCP-based multiplayer for local network play
  - Server runs on port 5420 with auto LAN IP detection
  - Real-time player position/rotation synchronization
  - Remote players appear as azure cubes
  - Support for multiple concurrent players
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

### Architecture

```text
mycraft/
├── engine/           # Core game logic
│   ├── game_app.py   # Main game entry point
│   ├── player.py     # Player entity with input handling
│   ├── input_handler.py # Movement and camera controls
│   ├── physics.py    # Reusable kinematic physics module
│   ├── world.py      # World generation
│   └── assets/       # Game assets
├── network/          # Multiplayer components
│   ├── server.py     # TCP server for LAN multiplayer
│   ├── client.py     # TCP client for connecting to games
│   └── protocol.py   # Message protocol definitions
├── util/             # Utilities (placeholder)
├── run_client.py     # Launch game client
└── run_server.py     # Launch LAN server
```

## Running the Game

### Single Player

```bash
python run_client.py
```

### LAN Multiplayer

#### Host (Server)

```bash
python run_server.py
```

The server will display your LAN IP address (e.g., `192.168.1.101:5420`).

#### Clients

```bash
python run_client.py --host 192.168.1.101 --port 5420
```

Replace the IP with the server's LAN IP. For local testing:

```bash
python run_client.py --host localhost --port 5420
```

#### Firewall Setup

Ensure port 5420 is allowed through your firewall:

```bash
sudo ufw allow 5420
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

## Future Plans

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
- **Physics**: Mario-style jumping with variable height, coyote time, and jump buffering

### Physics System

- **KinematicState**: Shared state container for vertical physics (velocity, grounded, timers)
- **Ground Detection**: Raycast-based ground height detection against chunk meshes
- **Jump Features**:
  - Variable jump height (tap = short hop, hold = full jump)
  - Coyote time (0.2s) for forgiving edge jumps
  - Jump buffering (0.2s) for pre-landing inputs
- **Reusable**: Physics module can be used by future entities (NPCs, enemies)

### Architecture

- **Modular Design**: Clear separation between Player, World, InputHandler, and Physics
- **Performance First**: Mesh optimization and chunk-based rendering
- **Documentation**: Entity sizing standards and world generation guidelines
