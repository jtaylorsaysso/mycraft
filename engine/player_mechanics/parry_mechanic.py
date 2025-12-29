"""Parry mechanic for player control system."""

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.input.keybindings import InputAction


class ParryMechanic(PlayerMechanic):
    """Handles parry input and publishes parry events.
    
    This mechanic detects parry input (Mouse2) and publishes
    a parry_input event for the ParrySystem to handle.
    """
    
    priority = 54  # Run after dodge (55), before camera (10)
    exclusive = False
    
    def __init__(self):
        self.parry_pressed_last_frame = False
    
    def can_handle(self, ctx: PlayerContext) -> bool:
        """Always enabled."""
        return True
    
    def update(self, ctx: PlayerContext) -> None:
        """Check for parry input and publish event.
        
        Args:
            ctx: Player context with input state
        """
        parry_pressed = ctx.input.is_action_active(InputAction.PARRY)
        
        # Detect rising edge (just pressed)
        if parry_pressed and not self.parry_pressed_last_frame:
            # Publish parry input event
            ctx.world.event_bus.publish("parry_input", entity_id=ctx.player_id)
        
        self.parry_pressed_last_frame = parry_pressed
