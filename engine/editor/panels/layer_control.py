from typing import Callable, Optional
from direct.gui.DirectGui import DirectButton, DGG
from panda3d.core import TextNode

from engine.editor.ui.theme import Colors, Spacing, TextScale
from engine.editor.ui.base_panel import FloatingPanel
from engine.editor.ui.widgets import EditorButton, EditorLabel


class LayerControl(FloatingPanel):
    """
    UI panel for controlling the active editing layer (Y-level).
    """
    
    def __init__(
        self,
        parent,
        on_layer_change: Optional[Callable[[int], None]] = None,
        min_layer: int = 0,
        max_layer: int = 15
    ):
        """
        Initialize layer controls.
        
        Args:
            parent: Parent GUI node
            on_layer_change: Callback when layer changes
            min_layer: Minimum Y-level
            max_layer: Maximum Y-level
        """
        super().__init__(parent, title="Layer", pos=(0, 0, 0))
        
        self.on_layer_change = on_layer_change
        self.min_layer = min_layer
        self.max_layer = max_layer
        self._current_layer = 0
        
        self._build_ui()
        
    def _build_ui(self):
        """Build the layer control UI."""
        # Current layer display
        self.layer_label = EditorLabel(
            parent=self.frame,
            text="Y: 0",
            scale="header",
            pos=(0, 0, 0.02),
            color="highlight",
            align="center"
        )
        
        # Up/Down buttons
        EditorButton(
            parent=self.frame,
            text="\u25b2", # Up Triangle
            pos=(-0.08, 0, -0.04),
            command=self._layer_up,
            size="small"
        )['frameSize'] = (-0.03, 0.03, -0.03, 0.03)
        
        EditorButton(
            parent=self.frame,
            text="\u25bc", # Down Triangle
            pos=(0.08, 0, -0.04),
            command=self._layer_down,
            size="small"
        )['frameSize'] = (-0.03, 0.03, -0.03, 0.03)
        
        # Quick layer buttons
        quick_y = -0.09
        for i, layer in enumerate([0, 5, 10, 15]):
            if layer <= self.max_layer:
                btn = EditorButton(
                    parent=self.frame,
                    text=str(layer),
                    pos=(-0.09 + i * 0.06, 0, quick_y),
                    command=self._set_layer,
                    extraArgs=[layer],
                    size="small"
                )
                btn['frameSize'] = (-0.025, 0.025, -0.025, 0.025)
                
    def _layer_up(self):
        """Increase layer by 1."""
        self._set_layer(min(self._current_layer + 1, self.max_layer))
        
    def _layer_down(self):
        """Decrease layer by 1."""
        self._set_layer(max(self._current_layer - 1, self.min_layer))
        
    def _set_layer(self, layer: int):
        """Set the current layer."""
        self._current_layer = layer
        self.layer_label["text"] = f"Y: {layer}"
        
        if self.on_layer_change:
            self.on_layer_change(layer)
            
    @property
    def current_layer(self) -> int:
        """Get the current layer."""
        return self._current_layer
        
    def set_layer(self, layer: int):
        """Programmatically set the layer."""
        self._set_layer(layer)
