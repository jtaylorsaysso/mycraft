from engine.ecs.system import System
from engine.ui.hud import HUD
from engine.ui.pause_overlay import PauseOverlay
from engine.ui.chat_overlay import ChatOverlay
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
        self.chat_overlay = None
        self.chest_overlay = None
        self.initialized = False
        self.chat_input_active = False
        self.chest_open = False
        
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
        
        # Initialize chat overlay
        self.chat_overlay = ChatOverlay(
            self.game,
            on_chat_opened=self._on_chat_opened,
            on_chat_closed=self._on_chat_closed
        )
        
        # Initialize chest overlay
        from engine.ui.chest_inventory_overlay import ChestInventoryOverlay
        
        # Get loot system for spawning pickups
        loot_system = self.world.get_system_by_type('LootSystem')
        
        self.chest_overlay = ChestInventoryOverlay(
            self.game,
            self.world,
            loot_system,
            on_close=self._on_chest_closed
        )
        
        # Subscribe to chest opened event
        self.event_bus.subscribe("chest_opened", self._on_chest_opened)
        
        # Key bindings - use Panda3D's accept() directly for reliability
        self.game.accept("escape", self._on_escape)
        self.game.accept("p", self._on_escape)  # P key as fallback
        self.game.accept("f3", self.toggle_debug)
        self.game.accept("t", self._on_chat_key)  # T key for chat
        
        print("✅ UISystem: Escape, P, F3, and T keys bound via accept()")
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
        """Handle escape key press - toggle pause or close overlays."""
        # Priority: close chest > close chat > toggle pause
        if self.chest_open:
            self.chest_overlay.close()
        elif self.chat_input_active:
            self.chat_overlay.close_input(send_message=False)
        else:
            self.toggle_pause()
    
    def _on_chat_key(self):
        """Handle T key press - open chat."""
        # Only open chat if not paused
        if self.game.game_state == GameState.PLAYING and not self.chat_input_active:
            self.chat_overlay.open_input()
    
    def _on_chat_opened(self):
        """Called when chat input is opened."""
        self.chat_input_active = True
        # Disable player movement input while chat is open
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.block_input("chat")
        logger.debug("Chat input opened - player input blocked")
    
    def _on_chat_closed(self):
        """Called when chat input is closed."""
        self.chat_input_active = False
        # Re-enable player movement input
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.unblock_input("chat")
        logger.debug("Chat input closed - player input restored")
    
    def _on_chest_opened(self, event):
        """Called when a chest is opened."""
        self.chest_open = True
        self.chest_overlay.open(event.chest_entity)
        
        # Pause game and show cursor
        from engine.game import GameState
        self.game.set_game_state(GameState.PAUSED)
        
        # Block player input
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.block_input("chest")
        logger.debug("Chest opened - game paused")
    
    def _on_chest_closed(self):
        """Called when chest UI is closed."""
        self.chest_open = False
        
        # Resume game and hide cursor
        from engine.game import GameState
        self.game.set_game_state(GameState.PLAYING)
        
        # Restore player input
        if hasattr(self.game, 'input_manager') and self.game.input_manager:
            self.game.input_manager.unblock_input("chest")
        logger.debug("Chest closed - game resumed")

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
        
        # Update chat overlay
        if self.chat_overlay:
            self.chat_overlay.update(dt)

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
        if self.chat_overlay:
            self.chat_overlay.cleanup()
        if self.chest_overlay:
            self.chest_overlay.cleanup()
        self.game.ignore("escape")
        self.game.ignore("p")
        self.game.ignore("f3")
        self.game.ignore("t")
