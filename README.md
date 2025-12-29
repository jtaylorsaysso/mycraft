# MyCraft – Action-RPG Voxel Engine

**A beginner-friendly voxel game engine** for creating exploration-driven action adventures. Build worlds with visual tools, then play them with friends—no coding required.

## Status

Build Status: Pre-alpha playtest  
**Visual Map Editor**: Coming in Milestone 3

**📖 [Engine Vision](VISION.md)** | **🎮 [Game Vision](VISION_VOXEL_WORLD.md)** | **🚧 [Boundaries](ENGINE_GAME_BOUNDARIES.md)** | **🗺️ [Roadmap](ROADMAP.md)**

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

## 🎨 What's Inside

MyCraft comes with **voxel_world**, an action-adventure game to explore:

- **9 Diverse Biomes**: Plains, forests, mountains, deserts, canyons, rivers, beaches, swamps, and rocky terrain
- **Movement-First Gameplay**: Sprint, climb, vault, and master momentum-based traversal
- **Timing-Based Combat**: Dodge, parry, and counterattack with skill-focused mechanics
- **Cooperative Multiplayer**: Adventure with friends on your local network
- **Customization**: Change textures, colors, and more *(visual tools coming soon!)*

### Coming Soon

- **Visual Map Editor** (Milestone 3): Design and build custom worlds
- **Character Customization** (Milestone 4): Skins, models, and rigging tools
- **Points of Interest**: Challenge shrines, dungeons, and epic boss encounters
- **Advanced Traversal**: Wall-running, grappling, and gliding mechanics

---

## 🔧 For Advanced Users

Want to dive deeper? MyCraft is built on a solid technical foundation:

- **Engine**: Powered by Panda3D with ECS architecture
- **Physics**: Kinematic character controller with slope handling
- **Networking**: TCP-based multiplayer with LAN discovery
- **Extensible**: Python-based, fully customizable

See the [Documentation](docs/index.md) for technical details and API references.

---

## 🤝 Contributing

Want to help make MyCraft better?

- **Playtesters**: Your feedback shapes the game! See [CONTRIBUTING.md](CONTRIBUTING.md) for how to report bugs and share ideas
- **Developers**: Check out [CONTRIBUTING.md](CONTRIBUTING.md) for setup, code style, and how to submit changes
- **Creators**: Share your custom content and ideas

---

## 📝 Summary

- **Target**: Absolute beginners who want to create voxel games
- **Stack**: Python 3.12 + Panda3D Engine
- **Status**: Pre-alpha playtest
- **Next Steps**: Visual editor (Milestone 3), customization tools (Milestone 4)
