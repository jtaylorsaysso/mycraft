# Physics System Documentation

## Overview

MyCraft uses a centralized kinematic physics system (`engine/physics/`) that provides reusable movement and jumping mechanics for entities. The system is designed for action-RPG style gameplay with smooth acceleration, responsive controls, and robust collision detection using Panda3D's collision system.

## Core Components

### KinematicState

Shared state container for entity physics:

- `velocity_x`: Current horizontal X velocity
- `velocity_y`: Current vertical velocity (Y-up in physics module)
- `velocity_z`: Current horizontal Z velocity
- `grounded`: Whether the entity is on the ground
- `time_since_grounded`: Time since last grounded (for coyote time)
- `time_since_jump_pressed`: Time since jump was requested (for jump buffering)

### Physics Constants (`engine/physics/constants.py`)

Centralized physics parameters for consistent behavior:

- `ACCELERATION`: 30.0 units/s² - Ground acceleration rate
- `FRICTION`: 15.0 units/s² - Deceleration when no input
- `AIR_CONTROL`: 0.5 - Multiplier for airborne acceleration
- `MOVE_SPEED`: 6.0 units/s - Base horizontal movement speed
- `WATER_MULTIPLIER`: 0.5 - Speed reduction in water
- `WATER_DRAG`: 2.0 - Drag coefficient in water
- `MAX_WALKABLE_SLOPE`: 45.0 - Max angle in degrees for walking
- `SLIDE_ACCELERATION`: 15.0 - Acceleration when sliding down steep slopes
- `SLIDE_FRICTION`: 5.0 - Reduced friction while sliding
- `SLIDE_CONTROL`: 0.3 - Player control multiplier when sliding

### Physics Functions

#### Gravity and Movement

- `apply_gravity(state, dt, gravity, max_fall_speed)`: Applies gravity to vertical velocity
- `apply_horizontal_acceleration(state, target_vel, dt, grounded)`: Smoothly accelerates/decelerates horizontal movement
- `apply_slope_forces(state, dt)`: Applies sliding forces on steep slopes
- `integrate_movement(entity, state, dt, ground_check, wall_check)`: Moves entity and resolves collisions

#### Jump Mechanics

- `perform_jump(state, jump_height)`: Sets jump velocity and adds slope-based boost
- `get_slope_velocity_component(state)`: Calculates velocity contribution from slope orientation
- `register_jump_press(state)`: Records a jump request for buffering
- `can_consume_jump(state, coyote_time, jump_buffer_time)`: Determines if buffered jump should execute
- `update_timers(state, dt)`: Advances coyote and jump buffer timers

#### Collision Detection

- `raycast_ground_height(entity, collision_traverser, render_node, ...)`: Raycasts down using Panda3D collision system
- `raycast_wall_check(entity, movement, collision_traverser, render_node, ...)`: Raycasts horizontally to detect walls

## Implementation Details

### Player Movement Parameters

The player uses responsive movement parameters:

- **Move Speed**: 6.0 units/s (base speed)
- **Acceleration**: 30.0 units/s² (snappy ground control)
- **Friction**: 15.0 units/s² (smooth deceleration)
- **Air Control**: 0.5 multiplier (limited airborne control)
- **Jump Height**: 1.2 units
- **Gravity**: -20.0 (snappy gravity)
- **Coyote Time**: 0.15s (forgiving edge jumps)
- **Jump Buffer**: 0.15s (pre-landing jump inputs)

### Horizontal Movement

Uses smooth acceleration model with:

- **Gradual acceleration** toward target speed
- **Friction-based deceleration** when no input
- **Boosted deceleration** when changing direction (2x friction when input opposes velocity)
- **Limited air control** (50% acceleration while airborne)

### Slope Physics & Sliding

The system handles angled terrain using surface normals:

- **Slope Detection**: Automatically calculates the slope angle from the ground surface normal.
- **Walkable Threshold**: Slopes up to 45° (configurable) are fully walkable.
- **Automatic Sliding**: On slopes steeper than the threshold, the entity enters a `sliding` state.
- **Momentum-based Sliding**: Sliding preserves horizontal momentum while adding a downslope acceleration component.
- **Limited Control**: Player has reduced horizontal control (30% by default) while sliding.
- **Jump Boosts**: Jumping while on a slope adds a velocity component from the slope's orientation.
  - **Uphill jumps** get an additional upward boost.
  - **Downhill jumps** get more horizontal distance but less height.

### Water Physics

Unified with ground physics via shared `KinematicState`:

- **Speed reduction**: 50% of base speed (WATER_MULTIPLIER)
- **Buoyancy**: Upward force applied to vertical velocity
- **Drag**: Exponential decay of all velocity components
- **Swimming**: Vertical control via jump input

### Collision Resolution

Uses Panda3D's collision system:

- **Terrain collision**: `CollisionPolygon` solids on chunk top faces AND side faces (East, West, South, North)
- **Ground detection**: Downward raycast from above entity
- **Wall detection**: Horizontal raycast in movement direction (enabled in `GroundMovementMechanic`)
- **Collision masks**: BitMask32.bit(1) for terrain layer
- **Side face generation**: Only creates collision for exposed faces (neighbor height is lower)
- **Performance**: Non-greedy meshing (one polygon per block face per vertical layer)

## Usage Pattern

```python
from engine.physics import (
    KinematicState, apply_gravity, apply_horizontal_acceleration,
    integrate_movement, can_consume_jump, perform_jump, update_timers
)
from engine.physics.constants import MOVE_SPEED

# In entity update loop
state = KinematicState()

# Horizontal movement
target_vel = move_direction * MOVE_SPEED
apply_horizontal_acceleration(state, (target_vel.x, target_vel.z), dt, state.grounded)

# Vertical movement
apply_gravity(state, dt, gravity=-20.0)

if can_consume_jump(state):
    perform_jump(state, jump_height=1.2)

# Integration with collision detection
def ground_check(entity):
    return raycast_ground_height(entity, collision_traverser, render_node)

def wall_check(entity, movement):
    return raycast_wall_check(entity, movement, collision_traverser, render_node)

integrate_movement(entity, state, dt, ground_check, wall_check)
update_timers(state, dt)
```

## Reusability

The physics module is designed to be reused by any entity:

- NPCs can create their own `KinematicState`
- Different gravity/jump parameters per entity type
- Different ground checks (flying entities, swimming, etc.)
- Shared acceleration and collision behavior

## Tuning Guidelines

### Movement Feel

- **Snappier**: Increase `ACCELERATION` and `FRICTION`
- **Floatier**: Decrease `ACCELERATION` and `FRICTION`
- **More responsive turns**: Increase boosted deceleration multiplier
- **More air control**: Increase `AIR_CONTROL` (max 1.0)

### Jump Feel

- **Higher jumps**: Increase `jump_height`
- **Floatier**: Make `gravity` less negative
- **Snappier**: Make `gravity` more negative
- **More forgiving**: Increase `coyote_time` and `jump_buffer_time`

### Performance Considerations

- Raycast collision detection is efficient with Panda3D's traverser
- Collision geometry only on visible chunk faces
- Physics updates are per-entity with KinematicState
- Wall sliding preserves momentum for smooth movement

## Completed Features

- ✅ Horizontal acceleration and deceleration
- ✅ Air control with configurable multiplier
- ✅ Panda3D collision system integration
- ✅ Wall collision with sliding
- ✅ Unified water physics
- ✅ Centralized physics constants
- ✅ Coyote time and jump buffering
- ✅ Variable jump height
- ✅ Slope handling and surface normal projection
- ✅ Sliding on steep slopes
- ✅ Side face collision geometry (2025-12-28) - Prevents phasing through vertical walls
- ✅ Wall collision checking enabled (2025-12-28) - `GroundMovementMechanic` now uses `raycast_wall_check`

## Future Extensions

### Planned Features

- Enhanced water physics (currents, waves)
- Ladder/climbable surface detection

### Entity-Specific Physics

- Flying entities with different gravity
- Enemies with custom movement patterns
- Vehicles with different acceleration curves

---

*Last Updated: 2025-12-28*
*Version: 3.1 - Side Face Collision & Wall Detection*
