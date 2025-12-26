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
        
    def setup(self, base):
        """Called by coordinator during initialize phase."""
        # Reuse global input manager if available, otherwise create one (fallback)
        if hasattr(base, 'input_manager') and base.input_manager:
            self.input_manager = base.input_manager
        else:
            self.input_manager = InputManager(base)
    
    def initialize(self, player_id, world):
        """Called when player is ready - setup for mouse locking."""
        # Cursor management is now handled by GameState
        # Initial lock happens when game enters PLAYING state
        print("🎮 Game starting - cursor will lock automatically")
        
    def can_handle(self, ctx: PlayerContext) -> bool:
        return True  # Always run
    
    def update(self, ctx: PlayerContext) -> None:
        if not self.input_manager:
            return
            
        # Update input manager
        self.input_manager.update()
        
        # Populate active actions
        active_actions = set()
        if hasattr(self.input_manager, 'key_bindings'):
            for key in self.input_manager.keys_down:
                actions = self.input_manager.key_bindings.get_actions_for_key(key)
                active_actions.update(actions)
        
        # Populate context.input
        ctx.input = InputState(
            mouse_delta=self.input_manager.mouse_delta,
            keys_down=self.input_manager.keys_down.copy(),
            actions=active_actions
        )
