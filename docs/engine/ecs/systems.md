# ECS Systems API - Quick Reference

> [!NOTE]
> This is a quick reference guide. A comprehensive deep dive tutorial is planned for a future update.

---

## Overview

Systems contain the logic that operates on entities with specific components. They run every frame and implement game behavior.

**Key Concepts**:

- Systems query entities with specific component combinations
- Each system focuses on one aspect of game logic (physics, rendering, AI)
- Systems communicate via the EventBus for decoupling

---

## Quick Start

```python
from engine.ecs.system import System
from engine.ecs.world import World
from engine.ecs.events import EventBus

class MovementSystem(System):
    def __init__(self, world: World, event_bus: EventBus):
        super().__init__(world, event_bus)
    
    def update(self, dt: float):
        # Find all entities with Position and Velocity
        for entity_id in self.world.get_entities_with(Position, Velocity):
            pos = self.world.get_component(entity_id, Position)
            vel = self.world.get_component(entity_id, Velocity)
            
            # Apply velocity
            pos.x += vel.x * dt
            pos.y += vel.y * dt
            pos.z += vel.z * dt

# Add to world
movement_system = MovementSystem(world, world.event_bus)
world.add_system(movement_system)
```

---

## System Base Class

### Constructor

```python
def __init__(self, world: World, event_bus: EventBus):
    super().__init__(world, event_bus)
    # Your initialization here
```

**Parameters**:

- `world`: Reference to the ECS world
- `event_bus`: Reference to the event system

**Attributes**:

- `self.world`: Access to entities and components
- `self.event_bus`: Publish and subscribe to events
- `self.enabled`: Boolean flag (default: `True`)

---

### Lifecycle Methods

#### `initialize()`

Called once when the system is added to the world.

```python
def initialize(self):
    # Set up event subscriptions
    self.event_bus.subscribe("player_spawned", self.on_player_spawn)
    
    # Initialize resources
    self.gravity = -9.8
```

#### `update(dt: float)`

Called every frame with delta time in seconds.

```python
def update(self, dt: float):
    # Process entities
    for entity_id in self.world.get_entities_with(Position, Velocity):
        # Game logic here
        pass
```

#### `cleanup()`

Called when the system is removed or the game ends.

```python
def cleanup(self):
    # Unsubscribe from events
    self.event_bus.unsubscribe("player_spawned", self.on_player_spawn)
    
    # Release resources
    self.texture_cache.clear()
```

---

## Common Patterns

### Query and Process Pattern

```python
class PhysicsSystem(System):
    def update(self, dt: float):
        # Query entities with required components
        entities = self.world.get_entities_with(Position, Velocity, RigidBody)
        
        for entity_id in entities:
            pos = self.world.get_component(entity_id, Position)
            vel = self.world.get_component(entity_id, Velocity)
            body = self.world.get_component(entity_id, RigidBody)
            
            # Apply physics
            vel.y += self.gravity * dt
            pos.x += vel.x * dt
            pos.y += vel.y * dt
            pos.z += vel.z * dt
```

### Event-Driven Updates

```python
class DamageSystem(System):
    def initialize(self):
        self.event_bus.subscribe("damage_dealt", self.on_damage)
    
    def on_damage(self, event):
        target_id = event.target_id
        damage = event.damage
        
        if self.world.has_component(target_id, Health):
            health = self.world.get_component(target_id, Health)
            health.current -= damage
            
            if health.current <= 0:
                self.event_bus.publish("entity_died", entity_id=target_id)
    
    def update(self, dt: float):
        # Event-driven, no frame update needed
        pass
```

### Conditional Processing

```python
class AISystem(System):
    def update(self, dt: float):
        for entity_id in self.world.get_entities_with(AIController, Position):
            ai = self.world.get_component(entity_id, AIController)
            
            # Only process active AI
            if not ai.active:
                continue
            
            # Update AI state
            ai.think(dt)
```

---

## System Communication

### Using Events

```python
class InventorySystem(System):
    def initialize(self):
        self.event_bus.subscribe("item_picked_up", self.on_item_pickup)
    
    def on_item_pickup(self, event):
        player_id = event.player_id
        item_type = event.item_type
        
        inventory = self.world.get_component(player_id, Inventory)
        inventory.add_item(item_type)
        
        # Notify other systems
        self.event_bus.publish("inventory_changed", player_id=player_id)
```

### Direct System Access

```python
class PlayerControlSystem(System):
    def update(self, dt: float):
        # Get terrain height from TerrainSystem
        terrain = self.world.get_system_by_type("TerrainSystem")
        if terrain:
            height = terrain.get_height_at(player_x, player_z)
```

---

## Enabling/Disabling Systems

```python
# Disable a system temporarily
physics_system.enabled = False

# Re-enable
physics_system.enabled = True
```

Disabled systems skip the `update()` call but remain in the world.

---

## Example Systems

### Simple Gravity System

```python
class GravitySystem(System):
    def __init__(self, world, event_bus):
        super().__init__(world, event_bus)
        self.gravity = -9.8
    
    def update(self, dt: float):
        for entity_id in self.world.get_entities_with(Velocity, Grounded):
            grounded = self.world.get_component(entity_id, Grounded)
            
            if not grounded.is_grounded:
                vel = self.world.get_component(entity_id, Velocity)
                vel.y += self.gravity * dt
```

### Cleanup System

```python
class CleanupSystem(System):
    def update(self, dt: float):
        entities_to_remove = []
        
        for entity_id in self.world.get_entities_with(Lifetime):
            lifetime = self.world.get_component(entity_id, Lifetime)
            lifetime.remaining -= dt
            
            if lifetime.remaining <= 0:
                entities_to_remove.append(entity_id)
        
        # Clean up after iteration
        for entity_id in entities_to_remove:
            self.world.destroy_entity(entity_id)
```

---

## Performance Tips

- **Cache queries**: Don't call `get_entities_with()` multiple times per frame
- **Early exit**: Skip processing if no entities match
- **Batch operations**: Group similar operations together
- **Profile systems**: Use `time_block()` from `util.logger` to measure performance

```python
from util.logger import time_block, get_logger

class ExpensiveSystem(System):
    def __init__(self, world, event_bus):
        super().__init__(world, event_bus)
        self.logger = get_logger("expensive_system")
    
    def update(self, dt: float):
        with time_block("expensive_system_update", self.logger):
            # Your expensive logic here
            pass
```

---

## System Execution Order

Systems execute in the order they were added to the world:

```python
# This order matters!
world.add_system(InputSystem(world, world.event_bus))      # 1. Read input
world.add_system(PhysicsSystem(world, world.event_bus))    # 2. Apply physics
world.add_system(CollisionSystem(world, world.event_bus))  # 3. Resolve collisions
world.add_system(RenderSystem(world, world.event_bus))     # 4. Render
```

---

## See Also

- [World API](world.md) - Entity and component management
- [Events API](events.md) - Event-driven communication
- [Physics System](../../physics_system.md) - Example system deep dive

---

> [!IMPORTANT]
> **TODO**: Comprehensive tutorial covering:
>
> - System design patterns and best practices
> - Inter-system dependencies and ordering
> - State management within systems
> - Testing and debugging systems
> - Performance profiling and optimization

---

*Last Updated: 2025-12-21*  
*API Version: 1.0*
