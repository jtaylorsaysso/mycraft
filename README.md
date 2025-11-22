# MyCraft - A Minecraft-like Game in Python

A simple 3D Minecraft-inspired game built with the Ursina engine.

## Features

### Current Implementation

- **3D World**: Flat grass terrain (20x20 blocks)
- **Player**: Simple block character with third-person over-the-shoulder camera
- **Movement Controls**:
  - **WASD**: Move forward/backward/strafe
  - **Mouse**: Rotate camera around player
  - **Space**: Jump
  - **Escape**: Toggle mouse lock

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

This is an **MVP (Minimum Viable Product)** with basic movement and world rendering. Future planned features:

- Block placement/destruction
- Multiplayer networking
- Terrain generation
- Inventory system
- Building mechanics

## Technical Notes

The game uses Ursina's Entity system for 3D rendering and includes:

- Custom InputHandler class for WASD movement and third-person camera control
- Gravity and jump mechanics
- Over-the-shoulder camera with proper rotation clamping
- Modular architecture ready for expansion
