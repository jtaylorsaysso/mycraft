# State Management

**For Advanced Users**

This document covers state management patterns in MyCraft, focusing on ECS component-based state, state machines, and event-driven transitions.

---

## Philosophy

MyCraft uses **ECS components as the single source of truth** for state. This avoids common anti-patterns like scattered boolean flags, mutable shared state, and tight coupling.

**Core Principle**: If state needs to persist across frames or be queried by multiple systems, **it belongs in a component**.

---

## Component-Based State

### The Pattern

```python
# ✅ GOOD: State in component
@dataclass
class CombatState:
    state: str = "idle"
    state_timer: float = 0.0
    can_attack: bool = True
    can_dodge: bool = True

# Systems query component
combat_state = world.get_component(entity_id, CombatState)
if combat_state.can_attack:
    # ...
```

```python
# ❌ BAD: State in system
class CombatSystem:
    def __init__(self):
        self.entity_states = {}  # Mutable dictionary
        self.is_attacking = False  # Boolean flag
```

### Why Components?

| Benefit | Explanation |
|:--|:--|
| **Queryable** | Any system can ask "is this entity attacking?" |
| **Serializable** | Save/load works automatically |
| **Testable** | Create test entities with specific states |
| **Debuggable** | Inspect component values in real-time |
| **Composable** | Add state without modifying systems |

---

## State Machine Components

State machines enforce valid transitions and prevent illegal states.

### Structure

```python
@dataclass
class <StateName>State:
    # Current state
    state: str = "default"
    state_timer: float = 0.0
    
    # State-specific data
    # ...
    
    # Action gates (booleans that control what actions are valid)
    can_<action>: bool = True
```

### Example: CombatState

```python
@dataclass
class CombatState:
    """Tracks player combat state and action availability."""
    
    # State machine
    state: str = "idle"  # idle | attacking | dodging | parrying | recovery
    state_timer: float = 0.0
    
    # Action gates
    can_attack: bool = True
    can_dodge: bool = True
    can_parry: bool = True
    can_cancel: bool = True
    
    # State data
    invincible: bool = False  # I-frames during dodge
```

**State Values**: Use strings for readability. Enum types also work for strict typing.

**State Timer**: Track time in current state for time-based transitions.

**Action Gates**: Boolean flags that systems check before allowing actions.

---

## State Transitions

### Event-Driven Pattern

State transitions are triggered by events published to the `EventBus`.

```python
# 1. Player presses attack button
event_bus.publish("attack_input", entity_id=player_id)

# 2. CombatSystem receives event
def on_attack_input(self, event):
    combat_state = self.world.get_component(event.entity_id, CombatState)
    
    # 3. Validate transition
    if not combat_state.can_attack:
        return  # Invalid state, reject
    
    # 4. Apply transition
    combat_state.state = "attacking"
    combat_state.state_timer = 0.0
    combat_state.can_attack = False
    combat_state.can_dodge = False
    
    # 5. Publish state change event
    event_bus.publish("attack_started", entity_id=event.entity_id)
```

### System-Driven Pattern

Systems update state based on timers or conditions.

```python
def update(self, dt: float):
    for entity_id in self.world.get_entities_with(CombatState):
        combat_state = self.world.get_component(entity_id, CombatState)
        
        # Update timer
        combat_state.state_timer += dt
        
        # Check for time-based transitions
        if combat_state.state == "attacking" and combat_state.state_timer >= 0.5:
            # Transition to recovery
            combat_state.state = "recovery"
            combat_state.state_timer = 0.0
        
        elif combat_state.state == "recovery" and combat_state.state_timer >= 0.15:
            # Transition to idle
            combat_state.state = "idle"
            combat_state.can_attack = True
            combat_state.can_dodge = True
```

---

## Example: CameraState

The `CameraState` component manages camera mode state.

### Component Definition

```python
@dataclass
class CameraState:
    """Camera mode and parameters."""
    mode: str = "EXPLORATION"  # FIRST_PERSON | EXPLORATION | COMBAT
    
    # Camera parameters
    yaw: float = 0.0
    pitch: float = 0.0
    zoom: float = 5.0
    
    # Bobbing state
    bob_offset_z: float = 0.0
```

### Mode Transitions

```python
class CameraMechanic(PlayerMechanic):
    def update(self, ctx: PlayerContext):
        camera_state = ctx.world.get_component(ctx.player_id, CameraState)
        
        # Check for mode toggle input (V key)
        if InputAction.CAMERA_TOGGLE_MODE in ctx.input.actions:
            # Cycle through modes
            if camera_state.mode == "FIRST_PERSON":
                camera_state.mode = "EXPLORATION"
            elif camera_state.mode == "EXPLORATION":
                camera_state.mode = "COMBAT"
            else:
                camera_state.mode = "FIRST_PERSON"
        
        # Apply mode-specific behavior
        camera = self.cameras[camera_state.mode]
        camera.update(cam_ctx)
```

---

## UI State Management

UI state follows the same component pattern for modal windows and overlays.

### Modal Stack Pattern

```python
@dataclass
class UIState:
    """Global UI state."""
    active_modals: List[str] = field(default_factory=list)
    input_blocked: bool = False

# Opening a modal
def open_settings():
    ui_state.active_modals.append("settings")
    ui_state.input_blocked = True

# Closing a modal
def close_settings():
    ui_state.active_modals.remove("settings")
    ui_state.input_blocked = len(ui_state.active_modals) > 0
```

### Editor State

The animation editor uses local state (not ECS) since it's a singleton tool window:

```python
class AnimationEditorWindow:
    def __init__(self):
        self.visible = False
        self.current_clip_name: Optional[str] = None
        self.playing = False
        self.current_time = 0.0

    def toggle(self):
        self.visible = not self.visible
        if not self.visible:
            self.playing = False  # Stop playback on close
```

**Why local state?** Editor is not an entity, it's a global UI tool. ECS is for game entities.

---

## Anti-Patterns to Avoid

### ❌ Scattered Boolean Flags

```python
# BAD: Flags in different places
class Player:
    is_attacking = False
    
class CombatSystem:
    is_player_dodging = False
    
class AnimationMechanic:
    can_move = True
```

**Problem**: No single source of truth, hard to query state.

**Solution**: Consolidate into `CombatState` component.

---

### ❌ Mutable Shared State

```python
# BAD: Systems share mutable dictionary
class GlobalState:
    player_states = {}  # Mutated by multiple systems

class CombatSystem:
    def update(self):
        GlobalState.player_states[player_id] = "attacking"

class AnimationSystem:
    def update(self):
        state = GlobalState.player_states.get(player_id)  # Race condition!
```

**Problem**: Race conditions, hard to debug, breaks component isolation.

**Solution**: Each system independently queries immutable component references.

---

### ❌ Implicit State Transitions

```python
# BAD: No validation, state changes anywhere
def on_attack(self):
    combat_state.state = "attacking"  # No checks!
    
def on_damage(self):
    combat_state.state = "idle"  # Overwrites attack state!
```

**Problem**: Invalid state transitions, unpredictable behavior.

**Solution**: Centralize transitions in dedicated systems, validate gates.

---

## State Validation

### Pre-Transition Checks

```python
def on_attack_input(self, event):
    combat_state = self.world.get_component(event.entity_id, CombatState)
    
    # Validate state allows attack
    if combat_state.state not in ["idle", "recovery"]:
        print(f"⚠️ Cannot attack from state: {combat_state.state}")
        return
    
    # Validate action gate
    if not combat_state.can_attack:
        print("⚠️ Attack is on cooldown")
        return
    
    # Transition is valid
    combat_state.state = "attacking"
```

### State Machine Diagram

Use diagrams to document valid transitions:

```text
┌──────┐    attack_input    ┌──────────┐
│ IDLE │──────────────────→│ATTACKING │
└──────┘                    └──────────┘
   ▲                             │
   │        duration_complete     │
   │                             ▼
   │                        ┌─────────┐
   └────────────────────────│RECOVERY │
              recovery_timer└─────────┘
```

---

## State Synchronization (Multiplayer)

In networked games, state must be synchronized across clients.

### Server Authority

```python
# Server owns state
@dataclass
class CombatState:
    state: str = "idle"
    # ... other fields
    
    def to_network_snapshot(self) -> dict:
        """Serialize for network."""
        return {
            'state': self.state,
            'state_timer': self.state_timer,
            'can_attack': self.can_attack
        }
    
    @classmethod
    def from_network_snapshot(cls, data: dict) -> 'CombatState':
        """Deserialize from network."""
        return cls(
            state=data['state'],
            state_timer=data['state_timer'],
            can_attack=data['can_attack']
        )
```

### Client Prediction

```python
# Client predicts state changes locally
def on_attack_input(self, event):
    # Immediate local state change (optimistic)
    combat_state.state = "attacking"
    
    # Send to server
    network_client.send_command("attack_input", entity_id=event.entity_id)
    
    # Server will send authoritative state in next snapshot
```

**Reconciliation**: Server snapshot overwrites client state if mismatch detected.

---

## Debugging State

### State Inspector

Add debug rendering to visualize state:

```python
def render_debug_ui(self):
    for entity_id in self.world.get_entities_with(CombatState):
        combat_state = self.world.get_component(entity_id, CombatState)
        transform = self.world.get_component(entity_id, Transform)
        
        # Render state above entity
        text = f"{combat_state.state} ({combat_state.state_timer:.2f}s)"
        self.render_text_3d(text, transform.position + LVector3f(0, 0, 2))
```

### State Logging

```python
def on_state_change(self, entity_id: str, old_state: str, new_state: str):
    print(f"🔄 {entity_id}: {old_state} → {new_state}")
```

### Assertions

```python
def update(self, dt: float):
    for entity_id in self.world.get_entities_with(CombatState):
        combat_state = self.world.get_component(entity_id, CombatState)
        
        # Validate state invariants
        assert combat_state.state in ["idle", "attacking", "dodging", "recovery"], \
            f"Invalid combat state: {combat_state.state}"
        
        assert combat_state.state_timer >= 0.0, \
            "State timer cannot be negative"
```

---

## Best Practices

### 1. Single Source of Truth

**Rule**: State lives in components, not systems.

```python
# ✅ GOOD
@dataclass
class MovementState:
    velocity: LVector3f
    grounded: bool

# ❌ BAD
class MovementSystem:
    def __init__(self):
        self.velocities = {}  # Duplicate of KinematicState
```

---

### 2. Immutable Queries

**Rule**: Components are queried, not stored.

```python
# ✅ GOOD
def update(self, dt):
    combat_state = self.world.get_component(entity_id, CombatState)
    combat_state.state = "attacking"  # Modify in-place

# ❌ BAD
def __init__(self):
    self.cached_combat_state = {}  # Stale data risk
```

---

### 3. Validate Before Transition

**Rule**: Always check gates before state changes.

```python
# ✅ GOOD
if combat_state.can_attack:
    combat_state.state = "attacking"

# ❌ BAD
combat_state.state = "attacking"  # No validation
```

---

### 4. Use Events for Cross-System Communication

**Rule**: Don't call other systems directly, publish events.

```python
# ✅ GOOD
self.event_bus.publish("attack_started", entity_id=entity_id)

# ❌ BAD
self.animation_system.play_attack()  # Tight coupling
```

---

## Testing State

### Unit Tests

```python
def test_attack_state_transition():
    world = World()
    entity = world.create_entity()
    world.add_component(entity, CombatState())
    
    combat_state = world.get_component(entity, CombatState)
    assert combat_state.state == "idle"
    assert combat_state.can_attack == True
    
    # Trigger transition
    combat_state.state = "attacking"
    combat_state.can_attack = False
    
    assert combat_state.state == "attacking"
    assert combat_state.can_attack == False
```

### Integration Tests

```python
def test_combat_state_flow():
    # Setup
    game = VoxelGame()
    player_id = game.world.get_entity_by_tag("player")
    
    # Attack
    game.world.event_bus.publish("attack_input", entity_id=player_id)
    
    # Verify state
    combat_state = game.world.get_component(player_id, CombatState)
    assert combat_state.state == "attacking"
    
    # Advance time to completion
    for _ in range(50):  # 0.5s at 100 FPS
        game.world.update(0.01)
    
    # Verify return to idle
    assert combat_state.state == "idle"
```

---

## Related Documentation

- [ECS: World](ecs/world.md) - Component management API
- [ECS: Events](ecs/events.md) - Event-driven architecture
- [Combat Architecture](COMBAT_ARCHITECTURE.md) - CombatState example
- [Player Mechanics](player_mechanics.md) - PlayerContext pattern

---

*Last Updated: 2025-12-30*  
*Version: 1.0*
