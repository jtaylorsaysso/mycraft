"""Input polling mechanic."""

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext, InputState
from engine.input.manager import InputManager

class InputMechanic(PlayerMechanic):
    """Handles input polling and updates context.input."""
    
    priority = 1000  # Run first
    exclusive = False
    
    def __init__(self, base):
        self.base = base
        self.input_manager = None
        self.esc_cooldown = 0.0  # Prevent ESC spam
        
    def setup(self, base):
        """Called by coordinator during initialize phase."""
        self.input_manager = InputManager(base)
    
    def initialize(self, player_id, world):
        """Called when player is ready - setup for mouse locking."""
        # Don't auto-lock - wait for user to click (like old system)
        print("🖱️ Click in window to lock mouse and start playing")
        
    def can_handle(self, ctx: PlayerContext) -> bool:
        return True  # Always run
    
    def update(self, ctx: PlayerContext) -> None:
        if not self.input_manager:
            return
            
        # Update input manager
        self.input_manager.update()
        
        # Update ESC cooldown
        self.esc_cooldown = max(0, self.esc_cooldown - ctx.dt)
        
        # Handle mouse locking/unlocking
        # Lock on mouse click if not locked
        if not self.input_manager.mouse_locked and self.input_manager.is_key_down('mouse1'):
            self.input_manager.lock_mouse()
            print("🖱️ Mouse locked - use ESC to unlock")
        
        # Unlock on ESC (with cooldown to prevent spam)
        if self.input_manager.mouse_locked and self.input_manager.is_key_down('escape') and self.esc_cooldown <= 0:
            self.input_manager.unlock_mouse()
            self.esc_cooldown = 0.5  # 500ms cooldown
            print("🖱️ Mouse unlocked - click to relock")
        
        # Populate context.input
        ctx.input = InputState(
            mouse_delta=self.input_manager.mouse_delta,
            keys_down=self.input_manager.keys_down.copy()
        )
