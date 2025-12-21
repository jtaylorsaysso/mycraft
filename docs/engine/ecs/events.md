# ECS Events API - Quick Reference

> [!NOTE]
> This is a quick reference guide. A comprehensive deep dive tutorial is planned for a future update.

---

## Overview

The `EventBus` provides publish-subscribe event communication for decoupling game systems. Systems can emit events without knowing who will handle them.

**Key Benefits**:

- Decouple systems (no direct dependencies)
- Flexible event handling (multiple subscribers)
- Easy to extend (add new handlers without modifying emitters)

---

## Quick Start

```python
from engine.ecs.events import EventBus, Event
from dataclasses import dataclass

# Create event bus
event_bus = EventBus()

# Define an event
@dataclass
class PlayerDied(Event):
    player_id: str
    cause: str

# Subscribe to events
def on_player_died(event: PlayerDied):
    print(f"Player {event.player_id} died from {event.cause}")

event_bus.subscribe("PlayerDied", on_player_died)

# Emit events
event = PlayerDied(player_id="player_123", cause="fall_damage")
event_bus.emit(event)
```

---

## EventBus API

### `subscribe(event_type: str, handler: Callable)`

Register a handler function for a specific event type.

```python
def on_damage(event):
    print(f"Entity {event.target_id} took {event.damage} damage")

event_bus.subscribe("damage_dealt", on_damage)
```

### `unsubscribe(event_type: str, handler: Callable)`

Remove a handler from an event type.

```python
event_bus.unsubscribe("damage_dealt", on_damage)
```

### `publish(event_name: str, **kwargs)`

Trigger an event with keyword arguments.

```python
# Simple event with data
event_bus.publish("item_collected", 
                  player_id=player, 
                  item_type="health_potion")
```

### `emit(event: Event)`

Emit a typed event object.

```python
@dataclass
class ItemCollected(Event):
    player_id: str
    item_type: str
    quantity: int

event = ItemCollected(player_id=player, item_type="gold", quantity=10)
event_bus.emit(event)
```

---

## Event Definition

### Simple Events (publish)

Use `publish()` for quick, ad-hoc events:

```python
# No class definition needed
event_bus.publish("player_jumped", player_id=player, height=2.5)
```

### Typed Events (emit)

Define event classes for structured data:

```python
from dataclasses import dataclass
from engine.ecs.events import Event

@dataclass
class DamageDealt(Event):
    source_id: str
    target_id: str
    damage: float
    damage_type: str

# Emit with type safety
event = DamageDealt(
    source_id=attacker,
    target_id=victim,
    damage=25.0,
    damage_type="physical"
)
event_bus.emit(event)
```

---

## Common Patterns

### System-to-System Communication

```python
class CombatSystem(System):
    def attack(self, attacker_id, target_id):
        # Calculate damage
        damage = self.calculate_damage(attacker_id)
        
        # Emit event instead of directly modifying health
        self.event_bus.publish("damage_dealt",
                               source_id=attacker_id,
                               target_id=target_id,
                               damage=damage)

class HealthSystem(System):
    def initialize(self):
        self.event_bus.subscribe("damage_dealt", self.on_damage)
    
    def on_damage(self, event):
        target_id = event.target_id
        health = self.world.get_component(target_id, Health)
        health.current -= event.damage
        
        if health.current <= 0:
            self.event_bus.publish("entity_died", entity_id=target_id)
```

### Multiple Subscribers

```python
# Multiple systems can react to the same event
class UISystem(System):
    def initialize(self):
        self.event_bus.subscribe("damage_dealt", self.show_damage_number)

class SoundSystem(System):
    def initialize(self):
        self.event_bus.subscribe("damage_dealt", self.play_hit_sound)

class ParticleSystem(System):
    def initialize(self):
        self.event_bus.subscribe("damage_dealt", self.spawn_blood_particles)
```

### Event Chains

```python
class InventorySystem(System):
    def initialize(self):
        self.event_bus.subscribe("item_collected", self.on_item_collected)
    
    def on_item_collected(self, event):
        inventory = self.world.get_component(event.player_id, Inventory)
        inventory.add(event.item_type)
        
        # Trigger another event
        self.event_bus.publish("inventory_changed", 
                               player_id=event.player_id,
                               item_type=event.item_type)

class QuestSystem(System):
    def initialize(self):
        self.event_bus.subscribe("inventory_changed", self.check_quest_progress)
    
    def check_quest_progress(self, event):
        # Check if collected item completes a quest
        pass
```

---

## Event Naming Conventions

**Recommended patterns**:

- **Past tense**: `player_died`, `item_collected`, `damage_dealt`
- **Descriptive**: `enemy_spawned`, `level_completed`, `door_opened`
- **Specific**: `player_health_changed` vs. `stat_changed`

**Event types**:

- **State changes**: `entity_died`, `player_spawned`
- **Actions**: `damage_dealt`, `item_used`
- **Triggers**: `area_entered`, `timer_expired`

---

## Error Handling

Event handlers are wrapped in try-except to prevent one handler from breaking others:

```python
def buggy_handler(event):
    raise Exception("Oops!")

def good_handler(event):
    print("This still runs!")

event_bus.subscribe("test_event", buggy_handler)
event_bus.subscribe("test_event", good_handler)

# Both handlers are called, error is logged
event_bus.publish("test_event")
```

Errors are logged but don't stop event propagation.

---

## Performance Considerations

### Minimize Event Spam

```python
# BAD: Emitting every frame
def update(self, dt):
    for entity_id in self.world.get_entities_with(Position):
        self.event_bus.publish("position_changed", entity_id=entity_id)

# GOOD: Only emit on significant changes
def update(self, dt):
    pos = self.world.get_component(player_id, Position)
    if abs(pos.x - self.last_x) > 1.0:  # Threshold
        self.event_bus.publish("player_moved_significantly", player_id=player_id)
        self.last_x = pos.x
```

### Batch Events

```python
# Instead of many small events
for item in collected_items:
    event_bus.publish("item_collected", item=item)

# Batch into one event
event_bus.publish("items_collected", items=collected_items)
```

---

## Debugging Events

### Event History

The EventBus maintains a history of events (useful for debugging):

```python
# Access event history
for event in event_bus._history:
    print(f"{event.__class__.__name__}: {event}")
```

### Logging Subscriptions

```python
# See what's subscribed to an event
subscribers = event_bus._subscribers.get("player_died", [])
print(f"Handlers for player_died: {[h.__name__ for h in subscribers]}")
```

---

## Example: Complete Event Flow

```python
# 1. Define events
@dataclass
class PlayerJumped(Event):
    player_id: str
    jump_height: float

# 2. System emits event
class PlayerControlSystem(System):
    def handle_jump_input(self, player_id):
        vel = self.world.get_component(player_id, Velocity)
        vel.y = 5.0  # Jump velocity
        
        # Notify other systems
        event = PlayerJumped(player_id=player_id, jump_height=5.0)
        self.event_bus.emit(event)

# 3. Other systems react
class AnimationSystem(System):
    def initialize(self):
        self.event_bus.subscribe("PlayerJumped", self.play_jump_animation)
    
    def play_jump_animation(self, event: PlayerJumped):
        # Trigger jump animation
        pass

class SoundSystem(System):
    def initialize(self):
        self.event_bus.subscribe("PlayerJumped", self.play_jump_sound)
    
    def play_jump_sound(self, event: PlayerJumped):
        # Play jump sound effect
        pass
```

---

## See Also

- [World API](world.md) - Entity and component management
- [Systems API](systems.md) - Creating game logic systems
- [Networking Guide](../../networking_guide.md) - Network event replication

---

> [!IMPORTANT]
> **TODO**: Comprehensive tutorial covering:
>
> - Event-driven architecture patterns
> - Event priority and ordering
> - Event filtering and routing
> - Network event synchronization
> - Event replay and debugging tools

---

*Last Updated: 2025-12-21*  
*API Version: 1.0*
