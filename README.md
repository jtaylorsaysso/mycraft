# MyCraft – Voxel Engine Experiment

A 3D voxel engine built with Ursina, focused on modular architecture, performance optimization, and multiplayer foundations.

## Overview

This project explores the core systems needed for a voxel-based engine with action-RPG elements. It emphasizes clean separation of concerns and performance-conscious design.

### Current Features

* **Chunk-Based Terrain**

  * Dynamic chunk loading with configurable radius
  * Infinite world exploration
  * 16×16 blocks per chunk with greedy meshing
  * Frustum culling and view distance control
  * Gentle rolling terrain with y=0 baseline

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

  * Per-chunk mesh aggregation with greedy meshing
  * Dynamic chunk loading/unloading for memory efficiency
  * Frustum culling to skip off-screen chunks
  * Throttled chunk generation to prevent frame drops

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

* Enhanced terrain generation (Perlin/Simplex noise, biomes)
* LOD system for distant chunks
* Multi-layer terrain and cave systems
* Action-RPG mechanics and entity interactions
* Texture atlas for varied block types
* Network optimizations (player interpolation, UDP)
* Persistence and save/load system for chunks and player state

## Dependencies

* Python 3.12+
* Ursina 8.2.0

## Installation

1. Clone the repository.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Tester Guide

### Quick Start
1. **Server**: Open a terminal and run `python run_server.py`.
2. **Client**: Open a separate terminal and run `python run_client.py --host localhost`.
   - You should spawn at `(10, 2, 10)` initially.
3. **Multiplayer**: To test with another computer on the same LAN:
   - Run server on host machine.
   - Run client on second machine: `python run_client.py --host <SERVER_LAN_IP>`.

### Common Issues
- **Firewall**: Ensure port 5420 is open if connecting from another machine.
- **Controls**: Press `Esc` to free your mouse cursor.
