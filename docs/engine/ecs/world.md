# ECS World API - Quick Reference

> [!NOTE]
> This is a quick reference guide. A comprehensive deep dive tutorial is planned for a future update.

---

## Overview

The `World` class is the main container for MyCraft's Entity Component System (ECS). It manages entities, components, and systems.

**Key Concepts**:

- **Entities**: Unique IDs representing game objects (players, blocks, NPCs)
- **Components**: Data containers attached to entities (Position, Velocity, Health)
- **Systems**: Logic that operates on entities with specific components

---

## Quick Start

```python
from engine.ecs.world import World
from engine.ecs.component import Component

# Create a world
world = World()

# Create an entity
player = world.create_entity(tag="player")

# Add components
class Position(Component):
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

world.add_component(player, Position(0, 10, 0))

# Query entities
entities_with_position = world.get_entities_with(Position)
```

---

## Core API

### Entity Management

#### `create_entity(tag: Optional[str] = None) -> str`

Create a new empty entity and return its unique ID.

```python
player = world.create_entity(tag="player")
enemy = world.create_entity()  # No tag
```

#### `get_entity_by_tag(tag: str) -> Optional[str]`

Get entity ID by tag name.

```python
player_id = world.get_entity_by_tag("player")
```

#### `destroy_entity(entity_id: str)`

Remove an entity and all its components.

```python
world.destroy_entity(enemy)
```

---

### Component Management

#### `add_component(entity_id: str, component: Component)`

Add a component to an entity.

```python
world.add_component(player, Velocity(0, 0, 0))
```

#### `get_component(entity_id: str, component_type: Type[T]) -> Optional[T]`

Get a specific component from an entity.

```python
pos = world.get_component(player, Position)
if pos:
    print(f"Player at ({pos.x}, {pos.y}, {pos.z})")
```

#### `has_component(entity_id: str, component_type: Type[Component]) -> bool`

Check if entity has a component.

```python
if world.has_component(player, Health):
    # Player can take damage
```

#### `remove_component(entity_id: str, component_type: Type[T])`

Remove a component from an entity.

```python
world.remove_component(player, Velocity)
```

#### `get_components(entity_id: str) -> Dict[Type[Component], Component]`

Get all components for an entity.

```python
all_components = world.get_components(player)
for comp_type, comp in all_components.items():
    print(f"{comp_type.__name__}: {comp}")
```

---

### Querying Entities

#### `get_entities_with(*component_types: Type[Component]) -> Set[str]`

Get all entity IDs that have ALL specified component types.

```python
# Find all entities with both Position and Velocity
moving_entities = world.get_entities_with(Position, Velocity)

for entity_id in moving_entities:
    pos = world.get_component(entity_id, Position)
    vel = world.get_component(entity_id, Velocity)
    # Update position based on velocity
```

---

### System Management

#### `add_system(system: System)`

Add a logic system to the world.

```python
from engine.systems.physics import PhysicsSystem

physics = PhysicsSystem(world, world.event_bus)
world.add_system(physics)
```

#### `get_system_by_type(system_name: str) -> Optional[System]`

Get a system by its class name.

```python
terrain = world.get_system_by_type("TerrainSystem")
if terrain:
    height = terrain.get_height_at(x, z)
```

#### `update(dt: float)`

Update all enabled systems.

```python
# In your game loop
world.update(delta_time)
```

---

## Common Patterns

### Creating a Game Object

```python
# Create player entity
player = world.create_entity(tag="player")

# Add components
world.add_component(player, Position(0, 50, 0))
world.add_component(player, Velocity(0, 0, 0))
world.add_component(player, Health(100))
world.add_component(player, Inventory())
```

### Iterating Over Entities

```python
# Find all entities that can move
for entity_id in world.get_entities_with(Position, Velocity):
    pos = world.get_component(entity_id, Position)
    vel = world.get_component(entity_id, Velocity)
    
    # Apply velocity to position
    pos.x += vel.x * dt
    pos.y += vel.y * dt
    pos.z += vel.z * dt
```

### Conditional Component Access

```python
# Check if entity has health before damaging
if world.has_component(entity_id, Health):
    health = world.get_component(entity_id, Health)
    health.current -= damage
    
    if health.current <= 0:
        world.destroy_entity(entity_id)
```

---

## Event System Integration

The `World` has an integrated `EventBus` for decoupled communication:

```python
# Access the event bus
world.event_bus.publish("player_died", player_id=player)

# Subscribe to events (usually in systems)
def on_player_spawn(event):
    player_id = event.player_id
    # Initialize player...

world.event_bus.subscribe("player_spawned", on_player_spawn)
```

See [events.md](events.md) for full EventBus documentation.

---

## Performance Tips

- **Batch queries**: Call `get_entities_with()` once, not in a loop
- **Cache components**: Store component references when possible
- **Use tags**: For frequently accessed entities like "player"
- **Remove unused components**: Clean up to reduce memory usage

---

## See Also

- [Systems API](systems.md) - Creating custom game logic
- [Events API](events.md) - Event-driven communication
- [Architecture Overview](../ARCHITECTURE.md) - ECS design philosophy

---

> [!IMPORTANT]
> **TODO**: Comprehensive tutorial covering:
>
> - Component design patterns
> - Entity lifecycle management
> - Performance optimization techniques
> - Advanced querying strategies
> - Debugging and introspection tools

---

*Last Updated: 2025-12-21*  
*API Version: 1.0*
