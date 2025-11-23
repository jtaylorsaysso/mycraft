# MyCraft – Voxel Engine Experiment

A 3D voxel engine built with Ursina, focused on modular architecture, performance optimization, and multiplayer foundations.

## Overview

This project explores the core systems needed for a voxel-based engine with action-RPG elements. It emphasizes clean separation of concerns and performance-conscious design.

### Current Features

* **Chunk-Based Terrain**

  * 3×3 chunk grid, 16×16 blocks per chunk
  * Gentle rolling terrain
  * Greedy meshing for top faces and side-face culling

* **Player**

  * 1.8 unit tall character
  * Third-person camera with collision prevention
  * Smooth movement, gravity, and jumping mechanics

* **Physics**

  * Kinematic controller for entities
  * Raycast-based ground detection
  * Jump buffering and coyote time

* **LAN Multiplayer**

  * TCP-based local network synchronization
  * Multi-player positions updated in real-time
  * Basic remote player visualization

* **Performance Optimizations**

  * Per-chunk mesh aggregation
  * Reduced draw calls and optimized rendering pipeline

### Controls

* **W/A/S/D** – Move relative to camera
* **Mouse** – Camera rotation around player
* **Space** – Jump
* **Escape** – Toggle/release cursor

## Architecture

```text
mycraft/
├── engine/           # Core game logic
│   ├── game_app.py
│   ├── player.py
│   ├── input_handler.py
│   ├── physics.py
│   ├── world.py
│   └── assets/
├── network/          # LAN multiplayer
│   ├── server.py
│   ├── client.py
│   └── protocol.py
├── util/             # Utilities
├── run_client.py
└── run_server.py
```

## Running the Game

**Single Player**

```bash
python run_client.py
```

**LAN Multiplayer**

**Server**

```bash
python run_server.py
```

**Client**

```bash
python run_client.py --host <server_ip> --port 5420
```

### Firewall

Allow port 5420 for LAN multiplayer:

```bash
sudo ufw allow 5420
```

## Roadmap

Planned features and improvements:

* Dynamic chunk loading and unloading
* Multi-layer terrain and varied biomes
* Action-RPG mechanics and entity interactions
* Expanded world generation
* Mesh and network optimizations for larger worlds
* Persistence and save/load system for chunks and player state

## Dependencies

* Python 3.12+
* Ursina 8.2.0
