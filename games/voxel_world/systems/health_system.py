"""
Health System.

Handles damage application and death events.
"""

from engine.ecs.system import System
from engine.components.core import Health, Transform
from engine.core.logger import get_logger

logger = get_logger(__name__)

class HealthSystem(System):
    """Manages health updates and death."""
    
    def initialize(self):
        self.event_bus.subscribe("on_entity_damage", self.on_entity_damage)
        
    def on_entity_damage(self, event):
        """Handle damage event."""
        target_id = event.target_id
        damage = event.damage
        
        health = self.world.get_component(target_id, Health)
        if not health:
            return
            
        if health.invulnerable:
            return
            
        health.current -= damage
        logger.info(f"💔 Entity {target_id} took {damage:.1f} damage. Health: {health.current:.1f}/{health.max_hp}")
        
        if health.current <= 0:
            self.die(target_id)
            
    def die(self, entity_id: str):
        """Handle entity death."""
        logger.info(f"💀 Entity {entity_id} died.")
        
        # Get position for death events (loot, fx)
        transform = self.world.get_component(entity_id, Transform)
        position = transform.position if transform else None
        
        # Publish death event
        self.event_bus.publish("entity_death", entity_id=entity_id, position=position)
        
        # Destroy entity
        self.world.destroy_entity(entity_id)
