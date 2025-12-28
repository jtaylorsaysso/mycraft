"""Attack mechanic for player control system."""

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.input.keybindings import InputAction


class AttackMechanic(PlayerMechanic):
    """Handles attack input and publishes attack events.
    
    This mechanic detects attack input (Mouse1) and publishes
    an attack_input event for the CombatSystem to handle.
    """
    
    priority = 53  # Run after parry (54), before camera (10)
    exclusive = False
    
    def __init__(self):
        self.attack_pressed_last_frame = False
    
    def can_handle(self, ctx: PlayerContext) -> bool:
        """Always enabled."""
        return True
    
    def update(self, ctx: PlayerContext) -> None:
        """Check for attack input and publish event.
        
        Args:
            ctx: Player context with input state
        """
        attack_pressed = ctx.input.is_action_active(InputAction.ATTACK_PRIMARY)
        
        # Detect rising edge (just pressed)
        if attack_pressed and not self.attack_pressed_last_frame:
            # Publish attack input event
            ctx.world.event_bus.publish("attack_input", entity_id=ctx.player_id)
        
        self.attack_pressed_last_frame = attack_pressed
