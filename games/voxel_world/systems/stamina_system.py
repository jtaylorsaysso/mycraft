"""Stamina regeneration system for combat and traversal mechanics."""

from engine.ecs.system import System
from engine.components.core import Stamina


class StaminaSystem(System):
    """Handles stamina regeneration with delay.
    
    Stamina regenerates at a fixed rate after a delay period following use.
    This applies to both combat actions (dodge, parry) and future traversal
    mechanics (sprint, climb, swim, vault).
    """
    
    def update(self, dt: float):
        """Update stamina regeneration for all entities with Stamina component.
        
        Args:
            dt: Delta time in seconds
        """
        for entity_id in self.world.get_entities_with(Stamina):
            stamina = self.world.get_component(entity_id, Stamina)
            
            # Only regenerate if below max
            if stamina.current < stamina.max_stamina:
                # Check if still in delay period
                if stamina.regen_timer > 0:
                    stamina.regen_timer -= dt
                else:
                    # Regenerate stamina
                    stamina.current = min(
                        stamina.max_stamina,
                        stamina.current + stamina.regen_rate * dt
                    )
