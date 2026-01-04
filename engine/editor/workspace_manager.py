"""
WorkspaceManager

Manages top-level workspace tabs and transitions.
Replaces the old vertical sidebar EditorSuiteManager.
"""

from typing import Dict, List, Optional
from direct.gui.DirectGui import DirectFrame, DirectButton, DGG
from panda3d.core import TextNode

from engine.editor.selection import EditorSelection
from engine.core.logger import get_logger

logger = get_logger(__name__)

class WorkspaceManager:
    """Manages workspace tabs and transitions."""
    
    def __init__(self, app):
        self.app = app
        self.workspaces: Dict[str, any] = {}
        self.workspace_order: List[str] = []
        self.active_workspace_name: Optional[str] = None
        
        # Shared state
        self.selection = EditorSelection()
        
        # UI
        self.top_bar = None
        self.tab_buttons: Dict[str, DirectButton] = {}
        
        self._build_ui()
        
    def _build_ui(self):
        """Build top horizontal tab bar."""
        # Top bar background
        self.top_bar = DirectFrame(
            parent=self.app.aspect2d,
            frameColor=(0.15, 0.15, 0.18, 1),
            frameSize=(-2.0, 2.0, 0.9, 1.0), # Top 10% of screen
            pos=(0, 0, 0),
            relief=DGG.FLAT
        )
        
        # Title (Left)
        from direct.gui.DirectGui import DirectLabel
        DirectLabel(
            parent=self.top_bar,
            text="MyCraft Editor",
            scale=0.04,
            pos=(-1.2, 0, 0.935),
            text_fg=(0.8, 0.8, 0.8, 1),
            text_align=TextNode.ALeft,
            frameColor=(0,0,0,0)
        )
        
    def add_workspace(self, name: str, workspace_instance):
        """Register a workspace."""
        self.workspaces[name] = workspace_instance
        self.workspace_order.append(name)
        
        # Inject selection if needed (though workspace base class handles it via app reference usually, 
        # but manual injection is safer)
        if hasattr(workspace_instance, 'set_selection'):
            workspace_instance.set_selection(self.selection)
            
        self._rebuild_tabs()
        
        # Activate first one automatically
        if len(self.workspaces) == 1:
            self.switch_to(name)
            
    def _rebuild_tabs(self):
        """Rebuild tab buttons."""
        # Cleanup old buttons
        for btn in self.tab_buttons.values():
            btn.destroy()
        self.tab_buttons.clear()
        
        start_x = -0.8
        spacing = 0.35
        
        for i, name in enumerate(self.workspace_order):
            x_pos = start_x + (i * spacing)
            
            is_active = (name == self.active_workspace_name)
            color = (0.3, 0.3, 0.35, 1) if is_active else (0.2, 0.2, 0.2, 0)
            text_color = (1, 1, 1, 1) if is_active else (0.6, 0.6, 0.6, 1)
            
            btn = DirectButton(
                parent=self.top_bar,
                text=name,
                scale=0.04,
                pos=(x_pos, 0, 0.935),
                frameColor=color,
                frameSize=(-0.16, 0.16, -0.025, 0.035),
                text_fg=text_color,
                command=self.switch_to,
                extraArgs=[name],
                relief=DGG.FLAT
            )
            self.tab_buttons[name] = btn

    def switch_to(self, name: str):
        """Switch active workspace."""
        if name not in self.workspaces:
            return
            
        if self.active_workspace_name == name:
            return
            
        # Exit current
        if self.active_workspace_name:
            current = self.workspaces[self.active_workspace_name]
            current.exit()
            
        # Enter new
        self.active_workspace_name = name
        new_ws = self.workspaces[name]
        new_ws.enter()
        
        # Update UI highlighting
        self._rebuild_tabs()
        
        logger.info(f"Switched to workspace: {name}")

    def update(self, dt):
        """Update active workspace."""
        if self.active_workspace_name:
            self.workspaces[self.active_workspace_name].update(dt)

    def cleanup(self):
        """Cleanup."""
        for ws in self.workspaces.values():
            ws.cleanup()
        if self.top_bar:
            self.top_bar.destroy()
