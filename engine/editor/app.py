"""
EditorApp: Standalone Panda3D application for editing tools.

Minimal runtime without ECS, gameplay systems, or world generation.
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, loadPrcFileData
from direct.gui.DirectGui import DirectLabel

from engine.editor.workspace_manager import WorkspaceManager
from engine.assets.manager import AssetManager
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
    
    Args:
        initial_workspace: Name of workspace to open initially (e.g., 'Character', 'Animation', 'Preview').
                          If None, defaults to "Character".
    """
    
    def __init__(self, initial_workspace: str = None):
        ShowBase.__init__(self)
        
        self._initial_workspace = initial_workspace or "Character"
        
        # Window setup
        props = WindowProperties()
        props.setTitle("MyCraft Editor Suite")
        if self.win:
            self.win.requestProperties(props)
            
        self.disableMouse()
        
        # Shared resources
        self.anim_registry = get_animation_registry()
        
        # Auto-scan animations directory
        from pathlib import Path
        anim_dir = Path(__file__).parent.parent.parent / "assets" / "animations"
        self.anim_registry.scan_directory(anim_dir)
        
        self.asset_manager = AssetManager("assets") # Default asset directory
        self.asset_manager.ensure_dir()
        
        # Workspace management
        self.workspace_manager = WorkspaceManager(self)
        
        # Import and register workspaces
        self._setup_workspaces()
        
        # Global shortcuts
        self.accept("escape", self.on_quit)
        
        # Status bar
        self._build_status_bar()
        
        logger.info("EditorApp initialized")
        
    def _setup_workspaces(self):
        """Import and register workspaces."""
        # Import workspaces
        from engine.editor.workspaces.character_workspace import CharacterWorkspace
        from engine.editor.workspaces.animation_workspace import AnimationWorkspace
        from engine.editor.workspaces.preview_workspace import PreviewWorkspace
        from engine.editor.workspaces.poi_workspace import POIWorkspace
        
        # Create and register
        self.workspace_manager.add_workspace("Character", CharacterWorkspace(self))
        self.workspace_manager.add_workspace("Animation", AnimationWorkspace(self))
        self.workspace_manager.add_workspace("Preview", PreviewWorkspace(self))
        self.workspace_manager.add_workspace("POI", POIWorkspace(self))
        
        # Switch to initial workspace if specified
        if self._initial_workspace and self._initial_workspace in self.workspace_manager.workspaces:
            self.workspace_manager.switch_to(self._initial_workspace)
        
    def _build_status_bar(self):
        """Build bottom status bar."""
        DirectLabel(
            parent=self.aspect2d,
            text="Space: Play | F: Frame | G/R/S: Transform | Ctrl+Z: Undo | ESC: Quit",
            scale=0.025,
            pos=(0, 0, -0.95),
            text_fg=(0.6, 0.6, 0.6, 1),
            frameColor=(0, 0, 0, 0)
        )
        
    def on_quit(self):
        """Handle quit request."""
        logger.info("Exiting editor")
        self.workspace_manager.cleanup()
        self.userExit()
        
    def run(self):
        """Start the editor application."""
        logger.info("Starting editor suite...")
        super().run()
