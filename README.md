# MyCraft – Playtest Build

A voxel engine experiment focused on performance and multiplayer.

## Status

Build Status: Pre-alpha playtest

---

## 🎮 How to Play (Playtesters Start Here)

### 1. Requirements

You need **Python 3.12+** installed on your computer.

- **Windows**: [Download Python](https://www.python.org/downloads/) (Check "Add Python to PATH" during install)
- **Mac**: `brew install python`
- **Linux**: `sudo apt install python3-full`

### 2. Install

Open your terminal or command prompt and run:

```bash
pip install -r requirements.txt
```

### 3. Launch the Game

We have a graphical launcher to make things easy.

**Windows:**
Double-click `launcher.py` in the folder.
*(If that doesn't work, right-click -> Open With -> Python)*

**Mac / Linux:**
Open terminal in this folder and run:

```bash
./launcher.py
```

### 4. Join a Game

- **Solo**: Just click **LAUNCH**.
- **Multiplayer**:
    1. One person runs `run_server.py` (or clicks "Launch Server" if we add that later).
    2. Everyone else opens the Launcher.
    3. Click **Refresh** to auto-detect the server on your WiFi.
    4. Click the server name and hit **LAUNCH**.

> **Need help regarding controls?** Check out the [Player Guide](PLAYER_GUIDE.md).

---

## 🛠️ For Developers (Technical Details)

### Core Features

- **Chunk-Based Terrain**: Infinite generation, greedy meshing, dynamic loading/culling.
- **Biome System**: 8 distinct biomes (Plains, Forest, Rocky, Desert, Mountain, Canyon, River, Beach, Swamp).
- **Texture Atlas**: 16x16 tile grid from `terrain.png` with per-face UV mapping.
- **Block Registry**: 19 block types with color fallback and texture support.
- **Physics**: Kinematic character controller, Mario-style jumping, collision handling.
- **Water Physics**: Buoyancy and swimming mechanics via `WaterPhysicsSystem`.
- **Networking**: TCP sync + UDP Broadcast discovery (Port 5420/5421).
- **Performance**: Frustum culling, throttled chunk generation.

### Architecture

```text
mycraft/
├── engine/           # Reusable Game Engine (ECS, Networking, Physics, Rendering)
│   ├── animation/    # Panda3D-based animation system
│   ├── core/         # Core utilities (logging, config)
│   ├── ecs/          # Entity Component System (World, Entity, Component, System)
│   ├── input/        # Input management (keyboard, mouse)
│   ├── networking/   # Client/Server networking + remote player rendering
│   ├── physics/      # Physics engine components
│   ├── rendering/    # Rendering utilities (camera, texture atlas, environment)
│   ├── systems/      # Core ECS systems (input, interaction, lifecycle, etc.)
│   └── ui/           # HUD and UI components
├── games/            # Specific game implementations
│   └── voxel_world/  # The main Voxel Game
│       ├── biomes/   # Biome definitions
│       ├── blocks/   # Block types
│       ├── config/   # Game configuration
│       └── systems/  # Game-specific systems (world gen, gameplay input)
├── launcher.py       # Tkinter GUI Entry Point
└── run_client.py     # CLI Entry Point
```

### Manual CLI Commands

If the launcher isn't your thing, you can use the CLI:

#### Server

```bash
python run_server.py --broadcast-rate 20
```

#### Client

```bash
python run_client.py --host 127.0.0.1 --preset creative --debug
```

### Troubleshooting

- **"Permission denied"**: Run `chmod +x *.py` on Mac/Linux.
- **Stuck Mouse**: Press `Esc` to unlock.
- **Firewall**: Ensure ports **5420 (TCP)** and **5421 (UDP)** are allowed.

---

## 📝 Summary

- **Target**: Casual playtesters & devs.
- **Stack**: Python 3.12 + Panda3D Engine.
- **Status**: Pre-alpha playtest.
- **Next Steps**: System completeness (server replication, inventory stacking), noise-based terrain, chat system.
