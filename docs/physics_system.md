# Physics System Documentation

## Overview

MyCraft uses a centralized kinematic physics system (`engine/physics.py`) that provides reusable movement and jumping mechanics for entities. The system is designed for action-RPG style gameplay with Mario-style jumping feel and robust ground detection.

## Core Components

### KinematicState

Shared state container for vertical physics:

- `velocity_y`: Current vertical velocity
- `grounded`: Whether the entity is on the ground
- `time_since_grounded`: Time since last grounded (for coyote time)
- `time_since_jump_pressed`: Time since jump was requested (for jump buffering)

### Physics Functions

#### Gravity and Movement

- `apply_gravity(state, dt, gravity, max_fall_speed)`: Applies gravity to vertical velocity
- `integrate_vertical(entity, state, dt, ground_check)`: Moves entity and resolves ground collisions

#### Jump Mechanics

- `perform_jump(state, jump_height)`: Sets jump velocity and clears buffers
- `register_jump_press(state)`: Records a jump request for buffering
- `can_consume_jump(state, coyote_time, jump_buffer_time)`: Determines if buffered jump should execute
- `update_timers(state, dt)`: Advances coyote and jump buffer timers

#### Ground Detection

- `raycast_ground_height(entity, ...)`: Raycasts down to find terrain height
- `simple_flat_ground_check(entity, ground_height)`: Fallback flat ground check

## Current Implementation

### Player Physics

The player uses Mario-style jumping parameters:

- **Jump Height**: 3.5 units (high, floaty jumps)
- **Gravity**: -8.0 (lighter than Earth gravity for floaty feel)
- **Max Fall Speed**: -20 (prevents excessive falling speed)
- **Coyote Time**: 0.2s (forgiving edge jumps)
- **Jump Buffer**: 0.2s (pre-landing jump inputs)
- **Variable Height**: Early release cuts velocity to 55% (tap = short hop)

### Ground Detection

Uses raycast-based detection against chunk meshes:

- Ray starts above the entity to avoid starting inside terrain
- Casts downward with sufficient distance (20 units)
- Returns ground height with foot offset for proper placement
- Ignores the entity itself to prevent self-collision

## Usage Pattern

```python
# In entity update loop
apply_gravity(state, dt, gravity=self.gravity, max_fall_speed=-20)

def ground_check(entity):
    return raycast_ground_height(entity)

integrate_vertical(entity, state, dt, ground_check=ground_check)
update_timers(state, dt)

if can_consume_jump(state, coyote_time=0.2, jump_buffer_time=0.2):
    perform_jump(state, jump_height)

# Variable jump height
if state.velocity_y > 0 and not held_keys['space']:
    state.velocity_y *= 0.55
```

## Reusability

The physics module is designed to be reused by any entity:

- NPCs can create their own `KinematicState`
- Different gravity/jump parameters per entity type
- Different ground checks (flying entities, swimming, etc.)
- Shared coyote/buffer behavior without code duplication

## Tuning Guidelines

### Making Jumps Feel Different

- **Higher jumps**: Increase `jump_height`
- **Floatier**: Make `gravity` less negative
- **Snappier**: Make `gravity` more negative
- **More forgiving**: Increase `coyote_time` and `jump_buffer_time`
- **Shorter taps**: Reduce the velocity multiplier in variable jump logic

### Performance Considerations

- Raycast ground detection is more expensive than flat checks but necessary for terrain
- Max fall speed prevents excessive velocity accumulation
- Physics updates are per-entity, so keep entity count reasonable

## Future Extensions

### Planned Features

- Horizontal acceleration and air control
- Slope handling and surface normal projection
- Wall sliding with forward raycasts
- Different ground checks for liquids, ladders, etc.

### Entity-Specific Physics

- Flying entities with different gravity
- Swimming with buoyancy
- Enemies with custom jump patterns

---

*Last Updated: 2025-11-22*
*Version: 1.0*
