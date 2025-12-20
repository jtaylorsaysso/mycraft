from engine.ecs.system import System
from engine.ecs.events import Event
from engine.components.core import Health, Transform
from engine.components.gameplay import Spawner
from engine.core.logger import get_logger
from typing import Any

logger = get_logger(__name__)

class DamageSystem(System):
    """Handles health reduction and death."""
    
    def initialize(self):
        self.event_bus.subscribe("on_entity_damage", self.on_damage)

    def update(self, dt: float):
        # Handle invulnerability timers
        for entity_id in self.world.get_entities_with(Health):
            health = self.world.get_component(entity_id, Health)
            if health.invulnerable and health.invuln_timer > 0:
                health.invuln_timer -= dt
                if health.invuln_timer <= 0:
                    health.invulnerable = False
                    health.invuln_timer = 0

    def on_damage(self, event: Any):
        entity_id = event.entity_id
        amount = event.amount
        source = getattr(event, 'source', None)

        health = self.world.get_component(entity_id, Health)
        if not health:
            return

        if health.invulnerable:
            return

        health.current -= amount
        logger.info(f"Entity {entity_id} took {amount} damage. Health: {health.current}/{health.max_hp}")
        
        if health.current <= 0:
            health.current = 0
            self.event_bus.publish("on_entity_death", entity_id=entity_id, killer=source)
            # Default behavior: destroy entity on death
            # In a real game, this might be overridden (ragdoll, respawn timer, etc)
            self.world.destroy_entity(entity_id)

class SpawnSystem(System):
    """Handles entity spawning from Spawner components."""
    
    def update(self, dt: float):
        for entity_id in self.world.get_entities_with(Spawner, Transform):
            spawner = self.world.get_component(entity_id, Spawner)
            transform = self.world.get_component(entity_id, Transform)
            
            # Clean up dead spawned entities
            spawner.spawned_ids = [eid for eid in spawner.spawned_ids 
                                 if self.world.get_components(eid)]
            
            if len(spawner.spawned_ids) >= spawner.max_active:
                continue
                
            spawner.timer += dt
            if spawner.timer >= spawner.interval:
                spawner.timer = 0
                self._spawn_entity(spawner, transform)

    def _spawn_entity(self, spawner: Spawner, transform: Transform):
        # In a real implementation, this would look up a prefab from a factory
        # For now, we just create a placeholder
        new_id = self.world.create_entity(tag=f"{spawner.entity_prefab}_{len(spawner.spawned_ids)}")
        
        # Add basic components
        self.world.add_component(new_id, Transform(
            position=transform.position, # Spawn at spawner location
            rotation=transform.rotation,
            scale=transform.scale
        ))
        
        spawner.spawned_ids.append(new_id)
        self.event_bus.publish("on_entity_spawn", entity_id=new_id, prefab=spawner.entity_prefab)
