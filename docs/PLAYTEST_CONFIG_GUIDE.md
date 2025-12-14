# MyCraft Playtest Configuration Guide

This guide explains how to tune the game experience for playtesting. Detailed configuration is available for both client (feel, visuals) and server (network, capacity).

## Quick Tuning (In-Game Commands)

The fastest way to tune the game is using slash commands. Press **T** to open the chat/command console.

### Common Tuning Commands
- **Move Faster**: `/set movement_speed 10` (Default: 6)
- **Jump Higher**: `/set jump_height 5` (Default: 3.5)
- **Adjust Gravity**: `/set gravity -15` (Default: -12, lower is floatier)
- **View Distance**: `/set view_distance 3` (Default: 5, lower improves FPS)
- **Mouse Sensitivity**: `/set mouse_sensitivity 30` (Default: 40)

> [!TIP]
> Use `/save` to permanently save your current settings to `config/playtest.json`.
> Use `/reload` to discard changes and reload from the file.

---

## Configuration Files

Files are located in the `config/` directory.

### Client Configuration (`config/playtest.json`)
Controls player feel, camera, animations, and graphics.
* **Auto-Reloads**: Yes. Edit this file while the game is running to see changes immediately.

**Key Parameters:**

| Category | Parameter | Default | Description |
|----------|-----------|---------|-------------|
| **Physics** | `movement_speed` | 6.0 | Player walking speed |
| | `fly_speed` | 12.0 | Flight speed in God Mode |
| | `jump_height` | 3.5 | Max jump height in blocks |
| | `gravity` | -12.0 | Gravity force (negative value) |
| **Camera** | `fov` | 90 | Field of View in degrees |
| | `camera_distance` | 4.0 | Distance behind player |
| | `camera_height` | 2.0 | Height above player pivot |
| | `camera_side_offset`| 1.0 | 1=Right shoulder, -1=Left |
| **Anim** | `walk_frequency` | 10.0 | Speed of walk cycle |
| | `walk_amplitude_arms`| 35.0 | Arm swing angle |
| | `idle_bob_amount` | 0.01 | Breathing animation intensity |
| **World** | `view_distance` | 5 | Render distance (chunks) |
| | `chunk_load_radius` | 3 | Chunks to keep loaded around player |

### Server Configuration (`config/server_config.json`)
Controls network settings and server capacity.
* **Auto-Reloads**: Yes (most settings).
* **Location**: Created automatically on first server run.

**Key Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `broadcast_rate` | 20 | Updates per second sent to clients. Higher = smoother but more bandwidth. |
| `max_players` | 16 | Max concurrent players. |
| `discovery_enabled`| true | Allow LAN auto-discovery. |
| `debug` | false | Enable verbose server logs. |
| `port` | 5420 | Server port (Requires restart to change). |

---

## Tuning Scenarios

### Scenario 1: "Movement feels too floaty"
The default gravity is fairly realistic but might feel slow for an arcade game.
* **Fix**: Increase gravity and jump height slightly to keep jump height same but make it faster.
* **Try**:
  ```
  /set gravity -18
  /set jump_height 4.5
  /save
  ```

### Scenario 2: "Animations look robotic"
If the walk cycle doesn't match the speed.
* **Fix**: Adjust `walk_frequency`.
* **Try**:
  ```
  /set walk_frequency 12
  /set walk_amplitude_arms 50
  /save
  ```

### Scenario 3: "Laggy on older laptop"
Reduce the workload on the client.
* **Fix**: Lower view distance and chunk loading.
* **Try**:
  ```
  /set view_distance 3
  /set chunk_load_radius 2
  /save
  ```

### Scenario 4: "Other players are lagging/teleporting"
Improve network update rate (requires Server Admin).
* **Fix**: Increase broadcast rate on the server console.
* **Try (Server Console)**:
  ```
  /set broadcast_rate 30
  ```
