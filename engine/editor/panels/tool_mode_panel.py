"""
Tool mode selector for the POI editor.

Provides buttons for switching between different editing tools.
"""

from typing import Callable, Optional
from direct.gui.DirectGui import DirectButton, DGG
from panda3d.core import TextNode

from engine.editor.ui.theme import Colors, Spacing, TextScale, FrameSize
from engine.editor.ui.base_panel import FloatingPanel
from engine.editor.ui.widgets import EditorButton
from engine.editor.ui.tooltip import Tooltip


class ToolModePanel(FloatingPanel):
    """
    Tool selection panel with brush, line, fill, and eraser modes.
    """
    
    TOOLS = [
        ("brush", "Brush", "Single block placement"),
        ("line", "Line", "Click and drag to draw lines"),
        ("fill", "Fill", "Flood fill bounded area"),
        ("eraser", "Eraser", "Remove blocks"),
    ]
    
    def __init__(
        self,
        parent,
        on_tool_change: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize tool mode panel.
        
        Args:
            parent: Parent GUI node
            on_tool_change: Callback when tool changes
        """
        # Wider frame for tools
        width = 0.35
        super().__init__(parent, title="Tools", pos=(0, 0, 0))
        # Override frame size for 4 buttons row
        self.frame['frameSize'] = (-width, width, -0.12, 0.12)
        # Move header to match
        self._header.setPos(-width + Spacing.PANEL_PADDING, 0, 0.12 - Spacing.PANEL_PADDING)
        
        self.on_tool_change = on_tool_change
        self._current_tool = "brush"
        self._buttons = {}
        self._tooltip = Tooltip(parent)
        
        self._build_ui()
        
    def _build_ui(self):
        """Build the tool buttons with tooltips."""
        # Tool buttons in a row
        # Start X based on 4 buttons with spacing
        count = len(self.TOOLS)
        btn_width = 0.14
        spacing = 0.02
        total_width = (count * btn_width) + ((count - 1) * spacing)
        start_x = -(total_width / 2) + (btn_width / 2)
        
        y = -0.04
        
        for i, (tool_id, label, tooltip_text) in enumerate(self.TOOLS):
            btn = EditorButton(
                parent=self.frame,
                text=label,
                pos=(start_x + i * (btn_width + spacing), 0, y),
                command=self._select_tool,
                extraArgs=[tool_id],
                size="small"
            )
            # Custom sizing for horizontal layout
            btn['text_scale'] = TextScale.SMALL
            btn['frameSize'] = (-0.06, 0.06, -0.025, 0.035)
            
            # Bind tooltip events
            btn.bind(DGG.ENTER, self._show_tooltip, [tooltip_text])
            btn.bind(DGG.EXIT, self._hide_tooltip)
            
            self._buttons[tool_id] = btn
            
        # Highlight default
        self._update_highlight()
        
    def _select_tool(self, tool_id: str):
        """Select a tool."""
        self._current_tool = tool_id
        self._update_highlight()
        
        if self.on_tool_change:
            self.on_tool_change(tool_id)
            
    def _update_highlight(self):
        """Update button highlighting."""
        for tool_id, btn in self._buttons.items():
            if tool_id == self._current_tool:
                btn["frameColor"] = Colors.BTN_SELECTED
                btn["text_fg"] = Colors.TEXT_PRIMARY
            else:
                btn["frameColor"] = Colors.BTN_DEFAULT
                btn["text_fg"] = Colors.TEXT_SECONDARY
                
    @property
    def current_tool(self) -> str:
        """Get the currently selected tool."""
        return self._current_tool
        
    def set_tool(self, tool_id: str):
        """Programmatically set the tool."""
        if tool_id in self._buttons:
            self._select_tool(tool_id)
            
    def _show_tooltip(self, text: str, event=None):
        """Show tooltip with tool description."""
        self._tooltip.show(text, event)
        
    def _hide_tooltip(self, event=None):
        """Hide tooltip."""
        self._tooltip.hide()
