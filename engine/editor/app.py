"""
EditorApp: Standalone Panda3D application for editing tools.

Minimal runtime without ECS, gameplay systems, or world generation.
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, loadPrcFileData
from direct.gui.DirectGui import DirectLabel

from engine.editor.manager import EditorSuiteManager
from engine.animation.animation_registry import get_animation_registry
from engine.core.logger import get_logger

logger = get_logger(__name__)

# Configure Panda3D for editor mode
loadPrcFileData("", """
    window-title MyCraft Editor Suite
    show-frame-rate-meter true
    sync-video false
""")


class EditorApp(ShowBase):
    """Standalone editor application.
    
    Runs without ECS, gameplay systems, or world generation.
    Provides shared resources for editor tools.
    """
    
    def __init__(self):
        ShowBase.__init__(self)
        
        # Window setup
        props = WindowProperties()
        props.setTitle("MyCraft Editor Suite")
        if self.win:
            self.win.requestProperties(props)
            
        self.disableMouse()
        
        # Shared resources
        self.anim_registry = get_animation_registry()
        
        # Editor suite management
        self.suite_manager = EditorSuiteManager(self)
        
        # Import and register editors
        self._setup_editors()
        
        # Global shortcuts
        self.accept("escape", self.on_quit)
        
        # Status bar
        self._build_status_bar()
        
        logger.info("EditorApp initialized")
        
    def _setup_editors(self):
        """Import and register editor tools."""
        # Import editors (lazy to avoid circular imports)
        from engine.editor.tools.model_editor import ModelEditor
        
        # Create and register editors
        model_editor = ModelEditor(self)
        self.suite_manager.add_editor("Model", model_editor)
        
        # Animation Editor
        from engine.editor.tools.animation_editor import AnimationEditor
        anim_editor = AnimationEditor(self)
        self.suite_manager.add_editor("Animation", anim_editor)
        
    def _build_status_bar(self):
        """Build bottom status bar."""
        DirectLabel(
            parent=self.aspect2d,
            text="1-9: Switch Editors | Ctrl+Z: Undo | Ctrl+Shift+Z: Redo | ESC: Quit",
            scale=0.025,
            pos=(0, 0, -0.95),
            text_fg=(0.6, 0.6, 0.6, 1),
            frameColor=(0, 0, 0, 0)
        )
        
    def on_quit(self):
        """Handle quit request."""
        logger.info("Exiting editor")
        self.suite_manager.cleanup()
        self.userExit()
        
    def run(self):
        """Start the editor application."""
        logger.info("Starting editor suite...")
        super().run()
