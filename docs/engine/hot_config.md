# HotConfig System

## Overview

The **HotConfig** system provides live-reload configuration for playtesting and development. It watches a JSON file for changes and automatically updates game settings in real-time, without restarting the game.

**Key Features**:

- File-based configuration (JSON)
- Automatic hot-reload when file changes
- Callback system for change notifications
- Singleton pattern for global access
- Default values with validation

---

## Architecture

```python
┌──────────────────────────────────────────────────┐
│              HotConfig Instance                  │
│  ┌────────────────────────────────────────────┐  │
│  │  config/playtest.json                      │  │
│  │  {                                         │  │
│  │    "mouse_sensitivity": 40.0,              │  │
│  │    "movement_speed": 6.0,                  │  │
│  │    "camera_distance": 4.0                  │  │
│  │  }                                         │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  File Watcher (checks every 1s)                  │
│  ↓                                                │
│  Detects changes → Reload → Notify callbacks     │
└──────────────────────────────────────────────────┘
```

**Location**: [engine/core/hot_config.py](file:///home/jamest/Desktop/dev/mycraft/engine/core/hot_config.py)

---

## Basic Usage

### Reading Configuration Values

```python
# In any system or mechanic
if hasattr(base, 'config_manager') and base.config_manager:
    sensitivity = base.config_manager.get("mouse_sensitivity", 40.0)
    fov = base.config_manager.get("fov", 90.0)
```

**Pattern**:

1. Check if `config_manager` exists
2. Call `get(key, default_value)`
3. Use the returned value

### Example: CameraMechanic Integration

From [camera_controller.py](file:///home/jamest/Desktop/dev/mycraft/engine/player_mechanics/camera_controller.py#L57-L70):

```python
def update(self, ctx: PlayerContext) -> None:
    # Update settings from config if available
    if hasattr(self.base, 'config_manager') and self.base.config_manager:
        sensitivity = self.base.config_manager.get("mouse_sensitivity", 40.0)
        fov = self.base.config_manager.get("fov", 90.0)
        
        # Apply FOV
        self.base.camLens.setFov(fov)
        
        # Apply sensitivity to all camera modes
        for camera in self.cameras.values():
            if hasattr(camera, 'set_sensitivity'):
                camera.set_sensitivity(sensitivity)
        
        # Apply camera distance (exploration/combat modes only)
        cam_dist = self.base.config_manager.get("camera_distance", 4.0)
        for mode in (CameraMode.EXPLORATION, CameraMode.COMBAT):
            cam = self.cameras.get(mode)
            if cam and hasattr(cam, 'set_distance'):
                cam.set_distance(camera_state, cam_dist)
```

**Result**: Players can edit `config/playtest.json` while the game is running, and camera settings update immediately.

---

## Integration Pattern

### 1. Initialization (Application Startup)

In `run_client.py` or game initialization:

```python
from engine.core.hot_config import HotConfig
from pathlib import Path

# Create config instance
config_path = Path("config/playtest.json")
config_manager = HotConfig(config_path, check_interval=1.0)

# Attach to base (ShowBase instance)
base.config_manager = config_manager
```

### 2. Update Loop (Every Frame)

In your main update loop:

```python
def update(self, dt):
    # Check for config changes
    if self.config_manager:
        if self.config_manager.update():
            print("🔄 Config reloaded!")
    
    # ... rest of update logic
```

The `update()` method:

- Returns `True` if config was reloaded
- Returns `False` if no changes detected
- Only checks file every `check_interval` seconds (default: 1.0)

### 3. Reading Values (In Systems/Mechanics)

```python
# Always provide a default value
speed = base.config_manager.get("movement_speed", 6.0)
gravity = base.config_manager.get("gravity", -12.0)
```

---

## Available Configuration Parameters

### Player Physics

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `mouse_sensitivity` | 40.0 | Camera rotation sensitivity |
| `movement_speed` | 6.0 | Player walking speed |
| `fly_speed` | 12.0 | Flight speed in god mode |
| `jump_height` | 3.5 | Maximum jump height |
| `gravity` | -12.0 | Gravity force (negative) |
| `god_mode` | false | Enable noclip flying |

### Camera

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `fov` | 90 | Field of view (degrees) |
| `camera_distance` | 4.0 | Third-person camera distance |
| `camera_height` | 2.0 | Camera height offset |
| `camera_side_offset` | 1.0 | Shoulder offset (1=right, -1=left) |
| `camera_auto_center_strength` | 0.3 | Strength of camera auto-drift (0-1) |
| `camera_auto_center_dead_zone` | 0.5 | Delay after mouse input (seconds) |

### Animations

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `walk_frequency` | 10.0 | Walk cycle speed |
| `walk_amplitude_arms` | 35.0 | Arm swing angle |
| `walk_amplitude_legs` | 30.0 | Leg swing angle |
| `idle_bob_speed` | 2.0 | Idle breathing speed |
| `idle_bob_amount` | 0.01 | Idle breathing intensity |

### World

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `view_distance` | 5 | Render distance (chunks) |
| `chunk_load_radius` | 3 | Chunks to keep loaded |
| `chunk_unload_radius` | 5 | Unload distance |
| `max_chunks_per_frame` | 1 | Chunk generation throttle |
| `debug_overlay` | false | Show debug HUD |

See `HotConfig.DEFAULTS` in [hot_config.py](file:///home/jamest/Desktop/dev/mycraft/engine/core/hot_config.py#L26-L54) for the complete list.

---

## Adding New Configuration Parameters

### 1. Add to DEFAULTS

Edit `engine/core/hot_config.py`:

```python
class HotConfig:
    DEFAULTS = {
        # ... existing defaults
        
        # Your new parameter
        "dash_speed": 15.0,
        "dash_duration": 0.3,
    }
```

### 2. Read in Your System

```python
class DashMechanic(PlayerMechanic):
    def update(self, ctx: PlayerContext) -> None:
        if hasattr(ctx.world.base, 'config_manager'):
            dash_speed = ctx.world.base.config_manager.get("dash_speed", 15.0)
            dash_duration = ctx.world.base.config_manager.get("dash_duration", 0.3)
        else:
            # Fallback if no config manager
            dash_speed = 15.0
            dash_duration = 0.3
        
        # Use values
        ctx.state.velocity = self.dash_direction * dash_speed
```

### 3. Document for Players

Add to [PLAYTEST_CONFIG_GUIDE.md](file:///home/jamest/Desktop/dev/mycraft/docs/PLAYTEST_CONFIG_GUIDE.md):

```markdown
| **Movement** | `dash_speed` | 15.0 | Dash velocity |
| | `dash_duration` | 0.3 | Dash duration (seconds) |
```

---

## Callback System

### Registering Callbacks

For systems that need to react immediately to config changes:

```python
def on_config_change(key: str, value: Any) -> None:
    print(f"Config changed: {key} = {value}")
    
    if key == "fov":
        # Update camera immediately
        base.camLens.setFov(value)

# Register callback
config_manager.on_change(on_config_change)
```

**Use cases**:

- Updating rendering settings that don't check every frame
- Logging configuration changes
- Invalidating caches when parameters change

---

## Advanced Features

### Saving Configuration

```python
# Modify in-game
config_manager.set("movement_speed", 10.0)

# Save to file
config_manager.save()
```

**Note**: Most systems only read config, they don't write it. Writing is typically done via in-game commands or UI.

### Creating Default Config File

```python
from pathlib import Path

config_manager = HotConfig()
config_manager.save_defaults(Path("config/playtest.json"))
```

This creates a JSON file with all default values, useful for:

- Initial setup
- Providing template for players
- Resetting to defaults

### Global Singleton Pattern

For systems that can't easily access `base.config_manager`:

```python
from engine.core.hot_config import init_config, get_config

# Initialize once at startup
init_config(Path("config/playtest.json"))

# Access anywhere
config = get_config()
if config:
    speed = config.get("movement_speed", 6.0)
```

**Recommendation**: Prefer passing `config_manager` explicitly over using the singleton.

---

## Best Practices

### 1. Always Provide Defaults

```python
# ✅ Good: Fallback if key missing
speed = config.get("movement_speed", 6.0)

# ❌ Bad: No fallback
speed = config.get("movement_speed")  # Returns None if missing!
```

### 2. Check for Config Manager Existence

```python
# ✅ Good: Safe check
if hasattr(base, 'config_manager') and base.config_manager:
    speed = base.config_manager.get("movement_speed", 6.0)
else:
    speed = 6.0  # Hardcoded fallback

# ❌ Bad: Assumes config_manager exists
speed = base.config_manager.get("movement_speed", 6.0)  # Crashes if None!
```

### 3. Read Config Once Per Frame

```python
# ✅ Good: Read once at start of update
def update(self, ctx):
    speed = ctx.world.base.config_manager.get("movement_speed", 6.0)
    # Use speed multiple times
    ...

# ❌ Bad: Read multiple times
def update(self, ctx):
    if ctx.input.forward:
        ctx.state.velocity.x = ctx.world.base.config_manager.get("movement_speed", 6.0)
    if ctx.input.back:
        ctx.state.velocity.x = -ctx.world.base.config_manager.get("movement_speed", 6.0)
```

### 4. Use Descriptive Parameter Names

```python
# ✅ Good: Clear and specific
"mouse_sensitivity"
"camera_distance"
"walk_frequency"

# ❌ Bad: Ambiguous
"sensitivity"  # Mouse? Controller? Audio?
"distance"     # Camera? Render? Interaction?
"frequency"    # Walk? Jump? What?
```

---

## Relationship to PLAYTEST_CONFIG_GUIDE.md

The [PLAYTEST_CONFIG_GUIDE.md](file:///home/jamest/Desktop/dev/mycraft/docs/PLAYTEST_CONFIG_GUIDE.md) is the **user-facing** documentation:

- Explains how to edit config files
- Provides tuning scenarios
- Lists all parameters with descriptions

This document (`hot_config.md`) is the **developer-facing** documentation:

- Explains how to integrate HotConfig into systems
- Shows code examples
- Describes architecture and patterns

---

## Troubleshooting

### Config Changes Not Applying

**Problem**: Edited `playtest.json` but changes don't take effect.

**Solutions**:

1. Check that `config_manager.update()` is called in the main loop
2. Verify the file path is correct
3. Ensure JSON syntax is valid (use a JSON validator)
4. Check that the system actually reads the parameter

### Config File Not Found

**Problem**: Game starts but config file doesn't exist.

**Solution**: Create default config:

```python
config_manager.save_defaults(Path("config/playtest.json"))
```

### Values Reverting

**Problem**: Changed values revert after a few seconds.

**Cause**: Another system is writing to config or file is being overwritten.

**Solution**: Check for `config_manager.save()` calls that might be resetting values.

---

## Related Documentation

- [PLAYTEST_CONFIG_GUIDE.md](../PLAYTEST_CONFIG_GUIDE.md) - User-facing configuration guide
- [Player Mechanics](player_mechanics.md) - How mechanics read HotConfig
- [Camera System](player_mechanics.md#cameramechanic-priority-10) - Camera HotConfig integration example

---

*Last Updated: 2025-12-28*  
*Version: 1.1*
