"""Dodge mechanic for player control system."""

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.input.keybindings import InputAction


class DodgeMechanic(PlayerMechanic):
    """Handles dodge input and publishes dodge events.
    
    This mechanic detects dodge input (Shift key) and publishes
    a dodge_input event for the DodgeSystem to handle.
    """
    
    priority = 55  # Run after ground movement (50), before camera (10)
    exclusive = False
    
    def __init__(self):
        self.dodge_pressed_last_frame = False
    
    def can_handle(self, ctx: PlayerContext) -> bool:
        """Always enabled."""
        return True
    
    def update(self, ctx: PlayerContext) -> None:
        """Check for dodge input and publish event.
        
        Args:
            ctx: Player context with input state
        """
        dodge_pressed = ctx.input.is_action_active(InputAction.DODGE)
        
        # Detect rising edge (just pressed)
        if dodge_pressed and not self.dodge_pressed_last_frame:
            # Publish dodge input event
            ctx.world.event_bus.publish("dodge_input", entity_id=ctx.player_id)
        
        self.dodge_pressed_last_frame = dodge_pressed
