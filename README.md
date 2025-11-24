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
  * Sword swing attack with hit detection, knockback, and visual/audio feedback
  * Safe hitbox management to avoid engine crashes

* **Combat System (Demo Room)**

  * Sword swing spawns short-lived hitbox with manual distance-based collision
  * Visual feedback: camera shake, enemy flash, particle burst on hit
  * 3-hit slime enemy with knockback and destruction
  * Safe particle effects using Ursina’s animate/destroy (no dynamic update assignment)

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
* **Left Mouse** – Sword swing attack
* **Escape** – Toggle/release cursor

### Demo Room

Run the combat sandbox demo:

```bash
python run_room1_demo.py
```

Features a 16x16 arena with a slime enemy to test combat mechanics.

## Architecture

```text
mycraft/
├── engine/           # Core game logic
│   ├── game_app.py
│   ├── player.py
│   ├── input_handler.py
│   ├── physics.py
│   ├── world.py
│   ├── room1_demo.py  # Demo room setup
│   └── assets/
├── network/          # LAN multiplayer
│   ├── server.py
│   ├── client.py
│   └── protocol.py
├── util/             # Utilities
├── run_client.py
├── run_server.py
└── run_room1_demo.py # Demo room entry point
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
* Simple slime AI (patrol → aggro → chase)
* Puzzle elements (pushable block, floor switch, door) for Room 1 completion

## Dependencies

* Python 3.12+
* Ursina 8.2.0
