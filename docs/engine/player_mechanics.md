# Player Mechanics System

## Overview

The Player Mechanics system provides a **composable, priority-based architecture** for handling all aspects of player control. Instead of a monolithic player controller, functionality is split into independent **mechanics** that can be added, removed, or reordered without affecting each other.

This pattern enables:

- **Modularity**: Each mechanic handles one concern (input, camera, movement, animation)
- **Extensibility**: Add new mechanics without modifying existing code
- **Testability**: Test mechanics in isolation
- **Flexibility**: Change behavior by swapping mechanics or adjusting priorities

---

## Architecture

### Core Components

```text
┌─────────────────────────────────────────────────────┐
│           PlayerControlSystem (Coordinator)         │
│  ┌───────────────────────────────────────────────┐  │
│  │  Mechanics (sorted by priority)               │  │
│  │  1. InputMechanic (1000)                      │  │
│  │  2. CameraMechanic (10)                       │  │
│  │  3. GroundMovementMechanic (50)               │  │
│  │  4. AnimationMechanic (5)                     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  Each frame:                                        │
│  1. Build PlayerContext (shared state)              │
│  2. Run mechanics in priority order                 │
│  3. Each mechanic reads/writes to context           │
└─────────────────────────────────────────────────────┘
```

### PlayerMechanic Base Class

All mechanics inherit from `PlayerMechanic`:

```python
from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext

class MyCustomMechanic(PlayerMechanic):
    priority = 50  # Higher runs first
    exclusive = False  # If True, stops processing after this
    
    def can_handle(self, ctx: PlayerContext) -> bool:
        """Return True if this mechanic should run this frame."""
        return True
    
    def update(self, ctx: PlayerContext) -> None:
        """Update player based on this mechanic."""
        # Read from context
        if ctx.input.forward:
            # Modify context
            ctx.state.velocity.y += 1.0
```

**Key attributes**:

- `priority` (int): Execution order (higher = earlier). Default: 50
- `exclusive` (bool): If True, stops processing remaining mechanics

**Key methods**:

- `can_handle(ctx)`: Gate to enable/disable mechanic based on state
- `update(ctx)`: Main logic, reads and modifies `PlayerContext`
- `cleanup()`: Optional cleanup when mechanic is removed

---

## PlayerContext

The `PlayerContext` is a shared data structure passed to all mechanics each frame. It contains:

### Core References

```python
@dataclass
class PlayerContext:
    world: World              # ECS world
    player_id: str            # Entity ID
    transform: Transform      # Position/rotation component
    state: KinematicState     # Physics state (velocity, grounded, etc.)
    dt: float                 # Delta time
```

### Input State

```python
    input: InputState         # Populated by InputMechanic
```

The `InputState` provides:

- `mouse_delta: tuple[float, float]` - Mouse movement this frame
- `keys_down: Set[str]` - Currently pressed keys
- `actions: Set[InputAction]` - Active actions (MOVE_FORWARD, JUMP, etc.)

**Convenience properties**:

```python
ctx.input.forward   # True if MOVE_FORWARD action active
ctx.input.back      # True if MOVE_BACK action active
ctx.input.left      # True if MOVE_LEFT action active
ctx.input.right     # True if MOVE_RIGHT action active
ctx.input.jump      # True if JUMP action active
ctx.input.crouch    # True if SLIDE or DODGE action active
```

### Shared State

```python
    camera_mode: str = 'third_person'  # Written by CameraMechanic
    terrain_system: Optional[object]   # Cached system references
    water_system: Optional[object]
```

Mechanics can write shared state that other mechanics read. For example:

- `CameraMechanic` writes `camera_mode`
- `AnimationMechanic` reads `camera_mode` to adjust animations

---

## Built-in Mechanics

### InputMechanic (Priority: 1000)

**Purpose**: Polls input and populates `ctx.input`

**Location**: [engine/player_mechanics/input_handler.py](file:///home/jamest/Desktop/dev/mycraft/engine/player_mechanics/input_handler.py)

**Responsibilities**:

- Calls `InputManager.update()` to calculate mouse delta
- Converts raw keys to actions via keybindings
- Populates `ctx.input.mouse_delta`, `ctx.input.keys_down`, `ctx.input.actions`

**Why priority 1000?** Must run first so all other mechanics have input data.

---

### CameraMechanic (Priority: 10)

**Purpose**: Handles camera mode switching and updates using a modular mode system

**Location**: [engine/player_mechanics/camera_controller.py](file:///home/jamest/Desktop/dev/mycraft/engine/player_mechanics/camera_controller.py)

**Responsibilities**:

- Manages a registry of camera modes (`FirstPersonCamera`, `ExplorationCamera`, `CombatCamera`)
- Detects V-key toggle via `InputAction.CAMERA_TOGGLE_MODE`
- Updates active camera using `CameraUpdateContext`
- Reads HotConfig for sensitivity, FOV, auto-centering strength, and camera distance

**Camera Modes**:

| Mode | Class | behavior |
| :--- | :--- | :--- |
| `FIRST_PERSON` | `FirstPersonCamera` | Direct control at eye eye-level |
| `EXPLORATION` | `ExplorationCamera` | Orbit with soft auto-centering (yaw/pitch) and bob |
| `COMBAT` | `CombatCamera` | Target framing with widened FOV |

**Example**:

```python
# Select camera from registry and update
self.active_camera = self.cameras.get(camera_state.mode)
self.active_camera.update(cam_ctx)
```

---

### GroundMovementMechanic (Priority: 50)

**Purpose**: Handles standard ground movement, jumping, physics

**Location**: [engine/player_mechanics/ground_movement.py](file:///home/jamest/Desktop/dev/mycraft/engine/player_mechanics/ground_movement.py)

**Responsibilities**:

- Calculates movement direction from input + camera heading
- Applies horizontal acceleration
- Handles gravity, jumping, slope forces
- Integrates movement with collision detection (ground + walls)
- Supports god mode (noclip flying)

**Collision Integration**:

```python
# Ground check for vertical collision
def ground_check(e):
    return raycast_ground_height(e, collision_traverser, render_node)

# Wall check for horizontal collision (2025-12-28: enabled)
def wall_check(e, move):
    return raycast_wall_check(e, move, collision_traverser, render_node)

integrate_movement(entity, state, dt, ground_check, wall_check)
```

**Example**:

```python
# Calculate movement direction
move_dir = LVector3f(0, 0, 0)
h = ctx.world.base.cam.getH()  # Camera heading
forward = LVector3f(-sin(h), cos(h), 0)

if ctx.input.forward: move_dir += forward
if ctx.input.back: move_dir -= forward
# ... apply physics
```

---

### AnimationMechanic (Priority: 5)

**Purpose**: Updates procedural character animations

**Location**: [engine/player_mechanics/animation.py](file:///home/jamest/Desktop/dev/mycraft/engine/player_mechanics/animation.py)

**Responsibilities**:

- Reads velocity to determine walk/idle state
- Applies procedural arm/leg swing
- Handles idle breathing animation
- Adjusts for camera mode (hide head in first-person)

**Why priority 5?** Runs last, after movement is finalized.

---

## PlayerControlSystem (Coordinator)

The `PlayerControlSystem` is an ECS system that coordinates all mechanics.

**Location**: [engine/systems/player_controller.py](file:///home/jamest/Desktop/dev/mycraft/engine/systems/player_controller.py)

### Lifecycle

#### 1. Initialization

```python
def __init__(self, world, event_bus, base):
    # Create mechanics
    self.mechanics = [
        InputMechanic(base),
        CameraMechanic(base),
        GroundMovementMechanic(),
        AnimationMechanic(base),
    ]
    
    # Sort by priority (highest first)
    self.mechanics.sort(key=lambda m: m.priority, reverse=True)
```

#### 2. Setup Phase

```python
def initialize(self):
    # Call setup() on mechanics that need it
    for mech in self.mechanics:
        if hasattr(mech, 'setup'):
            mech.setup(self.base)
```

The `setup()` method is for early initialization (e.g., `InputMechanic` creates `InputManager`).

#### 3. Ready Phase

```python
def on_ready(self):
    player_id = self.world.get_entity_by_tag("player")
    
    # Call initialize() on mechanics that need it
    for mech in self.mechanics:
        if hasattr(mech, 'initialize'):
            mech.initialize(player_id, self.world)
```

The `initialize()` method is called when the player entity is ready (e.g., `CameraMechanic` sets up cameras).

#### 4. Update Loop

```python
def update(self, dt):
    # Get player entity
    player_id = self.world.get_entity_by_tag("player")
    transform = self.world.get_component(player_id, Transform)
    state = self.physics_states[player_id]
    
    # Build context
    ctx = PlayerContext(
        world=self.world,
        player_id=player_id,
        transform=transform,
        state=state,
        dt=dt
    )
    
    # Run mechanics in priority order
    for mechanic in self.mechanics:
        if mechanic.can_handle(ctx):
            mechanic.update(ctx)
            if mechanic.exclusive:
                break  # Stop processing
    
    # Clear transition requests
    ctx.clear_requests()
```

---

## Creating Custom Mechanics

### Example: Climbing Mechanic

```python
from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.input.keybindings import InputAction

class ClimbingMechanic(PlayerMechanic):
    priority = 60  # Higher than GroundMovement (50)
    exclusive = True  # Prevent ground movement while climbing
    
    def can_handle(self, ctx: PlayerContext) -> bool:
        # Only run if player is near climbable surface
        return self._is_near_climbable_surface(ctx)
    
    def update(self, ctx: PlayerContext) -> None:
        # Vertical movement
        if ctx.input.forward:
            ctx.state.velocity.z = 2.0  # Climb up
        elif ctx.input.back:
            ctx.state.velocity.z = -2.0  # Climb down
        else:
            ctx.state.velocity.z = 0.0
        
        # Horizontal movement along wall
        # ... climbing logic
        
        # Jump to dismount
        if ctx.input.jump:
            ctx.state.velocity = self._calculate_dismount_velocity(ctx)
            # Request ground movement for next frame
            ctx.request_mechanic('ground_movement')
    
    def _is_near_climbable_surface(self, ctx):
        # Raycast to detect climbable wall
        # ...
        return False
```

### Registering Custom Mechanics

Add to `PlayerControlSystem.__init__()`:

```python
self.mechanics = [
    InputMechanic(base),
    CameraMechanic(base),
    ClimbingMechanic(),        # Add custom mechanic
    GroundMovementMechanic(),
    AnimationMechanic(base),
]
```

The system automatically sorts by priority.

---

## Priority System

Mechanics execute in **descending priority order** (highest first):

| Mechanic | Priority | Reason |
| :--- | :--- | :--- |
| InputMechanic | 1000 | Must populate input first |
| ClimbingMechanic | 60 | Check special movement before ground |
| GroundMovementMechanic | 50 | Default movement |
| CameraMechanic | 10 | Update camera after movement |
| AnimationMechanic | 5 | Animate based on final state |

**Guidelines**:

- **Input polling**: 900-1000
- **Special movement** (climbing, gliding): 60-100
- **Default movement**: 40-60
- **Camera**: 10-20
- **Visual effects** (animation, particles): 0-10

---

## Best Practices

### 1. Keep Mechanics Focused

Each mechanic should handle **one concern**:

- ✅ `CameraMechanic` handles camera
- ❌ Don't add movement logic to `CameraMechanic`

### 2. Use `can_handle()` for State Gates

```python
def can_handle(self, ctx: PlayerContext) -> bool:
    # Don't run if climbing
    if ctx.state.climbing:
        return False
    return True
```

### 3. Write Shared State to Context

If other mechanics need your state, write to context:

```python
# In ClimbingMechanic
ctx.state.climbing = True  # Other mechanics can check this
```

### 4. Use `exclusive` Sparingly

Only set `exclusive = True` if you want to **completely override** remaining mechanics:

```python
class CutsceneMechanic(PlayerMechanic):
    priority = 200
    exclusive = True  # Disable all player control
```

### 5. Read HotConfig for Tunables

```python
if hasattr(ctx.world.base, 'config_manager'):
    speed = ctx.world.base.config_manager.get("climb_speed", 2.0)
```

---

## Testing Mechanics

Mechanics can be tested in isolation:

```python
def test_climbing_mechanic():
    # Create mock context
    ctx = PlayerContext(
        world=mock_world,
        player_id="player_1",
        transform=Transform(position=LVector3f(0, 0, 0)),
        state=KinematicState(),
        dt=0.016
    )
    
    # Simulate input
    ctx.input.forward = True
    
    # Run mechanic
    mechanic = ClimbingMechanic()
    mechanic.update(ctx)
    
    # Assert behavior
    assert ctx.state.velocity.z == 2.0
```

---

## Common Patterns

### State Machines

Use `can_handle()` to implement state-based behavior:

```python
class GlidingMechanic(PlayerMechanic):
    def can_handle(self, ctx: PlayerContext) -> bool:
        # Only glide if airborne and glider equipped
        return not ctx.state.grounded and ctx.state.has_glider
```

### Transition Requests

Request a specific mechanic for next frame:

```python
# In ClimbingMechanic
if ctx.input.jump:
    ctx.request_mechanic('ground_movement')
```

### Temporary Overrides

Use high priority + exclusive for temporary control:

```python
class DashMechanic(PlayerMechanic):
    priority = 100
    exclusive = True
    
    def __init__(self):
        self.dash_timer = 0.0
    
    def can_handle(self, ctx):
        return self.dash_timer > 0
    
    def update(self, ctx):
        # Override movement during dash
        ctx.state.velocity = self.dash_direction * 20.0
        self.dash_timer -= ctx.dt
```

---

## Debugging

The coordinator prints execution order on startup:

```text
🔧 Mechanic execution order (priority):
   - InputMechanic: priority=1000
   - CameraMechanic: priority=10
   - GroundMovementMechanic: priority=50
   - AnimationMechanic: priority=5
```

Add debug prints in your mechanic:

```python
def update(self, ctx):
    print(f"🧗 Climbing: velocity={ctx.state.velocity}")
```

---

## Related Documentation

- [Input System](../input/README.md) - How input is polled and mapped to actions
- [Physics System](../physics_system.md) - Physics functions used by movement mechanics
- [HotConfig](hot_config.md) - Runtime configuration system
- [ECS Architecture](ARCHITECTURE.md) - Overall engine architecture

---

*Last Updated: 2025-12-28*  
*Version: 1.1*
