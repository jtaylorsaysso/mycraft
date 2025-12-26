from engine.ecs.system import System
from engine.ui.hud import HUD
from engine.ui.pause_overlay import PauseOverlay
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
        self.pause_overlay = None
        self.initialized = False
        
    def initialize(self):
        """Called when system is added"""
        # Initialize HUD
        self.hud = HUD(self.game, world=self.world, networking=False, hot_config=self.hot_config)
        self.hud.show_welcome_message("Welcome to MyCraft!")
        
        # Initialize pause overlay (always exists)
        self.pause_overlay = PauseOverlay(
            self.game,
            on_resume=self._on_resume,
            on_quit=None  # TODO: Add quit to menu functionality
        )
        
        # Key bindings - use Panda3D's accept() directly for reliability
        self.game.accept("escape", self._on_escape)
        self.game.accept("p", self._on_escape)  # P key as fallback
        self.game.accept("f3", self.toggle_debug)
        
        print("✅ UISystem: Escape and P keys bound via accept()")
        logger.info("UISystem initialized")
        self.initialized = True

    def on_ready(self):
        """Called when game is starting"""
        super().on_ready()  # CRITICAL: Sets ready=True so update() runs!
        
        # Find player to track
        player_id = self.world.get_entity_by_tag("player")
        if player_id:
            self.hud.player_entity_id = player_id

    def _on_escape(self):
        """Handle escape key press - toggle pause."""
        self.toggle_pause()

    def update(self, dt):
        """Update UI elements."""
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
            
            # Sync pause overlay with pause state
            if self.game.game_state == GameState.PAUSED:
                if not self.pause_overlay.visible:
                    self.pause_overlay.show()
                # Also show settings if available
                if self.hud.settings and not self.hud.settings.visible:
                    self.hud.settings.show()
            else:  # PLAYING or MENU
                if self.pause_overlay.visible:
                    self.pause_overlay.hide()
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

    
    def _on_resume(self):
        """Handle resume from pause overlay."""
        self.game.set_game_state(GameState.PLAYING)
            
    def cleanup(self):
        if self.hud:
            self.hud.cleanup()
        if self.pause_overlay:
            self.pause_overlay.cleanup()
        self.game.ignore("escape")
        self.game.ignore("p")
        self.game.ignore("f3")
