from engine.ecs.system import System
from engine.ui.hud import HUD
from engine.core.logger import get_logger
from engine.game import GameState

logger = get_logger("systems.ui")

class UISystem(System):
    """Manages the In-Game HUD and UI interactions."""
    
    def __init__(self, world, event_bus, game, hot_config=None):
        super().__init__(world, event_bus)
        self.game = game
        self.hot_config = hot_config
        self.hud = None
        self.initialized = False
        
    def initialize(self):
        """Called when system is added"""
        # We need the player entity to fully init the HUD, but we can start basic
        # The HUD class expects player_entity_id, which might not be ready.
        # We can pass None and update it later.
        self.hud = HUD(self.game, world=self.world, networking=False, hot_config=self.hot_config)
        self.hud.show_welcome_message("Welcome to MyCraft!")
        
        # Key bindings
        self.game.accept("f3", self.toggle_debug)
        self.game.accept("escape", self.toggle_pause)  # Changed to toggle_pause
        
        logger.info("UISystem initialized")
        self.initialized = True

    def on_ready(self):
        """Called when game is starting"""
        # Find player to track
        player_id = self.world.get_entity_by_tag("player")
        if player_id:
            self.hud.player_entity_id = player_id

    def update(self, dt):
        if self.hot_config:
            self.hot_config.update()
            
        if self.hud:
            # Sync player ID if missed in on_ready
            if not self.hud.player_entity_id:
                self.hud.player_entity_id = self.world.get_entity_by_tag("player")
            
            # Sync debug visibility from config
            if self.hot_config:
                self.hud.debug_visible = self.hot_config.get("debug_overlay", False)
                if self.hud.debug_visible:
                    self.hud.pos_text.show()
                else:
                    self.hud.pos_text.hide()
            
            # Sync settings overlay with pause state
            if self.game.game_state == GameState.PAUSED:
                if self.hud.settings and not self.hud.settings.visible:
                    self.hud.settings.show()
            else:  # PLAYING or MENU
                if self.hud.settings and self.hud.settings.visible:
                    self.hud.settings.hide()
                
            self.hud.update(dt)

    def toggle_debug(self):
        if self.hot_config:
            current = self.hot_config.get("debug_overlay", False)
            self.hot_config.set("debug_overlay", not current)
        elif self.hud:
            self.hud.toggle_debug()
    
    def toggle_pause(self):
        """Toggle pause state (Escape key).
        
        This automatically manages cursor lock/unlock via GameState.
        """
        self.game.toggle_pause()
        logger.debug(f"Pause toggled: {self.game.game_state.name}")
            
    def cleanup(self):
        if self.hud:
            self.hud.cleanup()
        self.game.ignore("f3")
        self.game.ignore("escape")
