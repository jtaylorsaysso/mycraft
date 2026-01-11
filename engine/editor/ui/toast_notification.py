"""
Toast notification widget for editor feedback.

Display temporary fade-in/fade-out messages for save/load status,
errors, and other user feedback.
"""

from typing import Optional, Tuple
from direct.gui.DirectGui import DirectLabel, DGG
from direct.interval.LerpInterval import LerpColorScaleInterval
from direct.interval.IntervalGlobal import Sequence, Wait, Func

from engine.editor.ui.theme import Colors, TextScale


class ToastNotification:
    """Temporary on-screen notification for editor feedback."""
    
    def __init__(self, parent):
        """
        Initialize toast notification system.
        
        Args:
            parent: Parent GUI node (typically aspect2d)
        """
        self.parent = parent
        self._label: Optional[DirectLabel] = None
        self._sequence: Optional[Sequence] = None
        
    def show(
        self, 
        message: str, 
        duration: float = 2.0, 
        color: Tuple[float, float, float, float] = (0.2, 0.6, 0.2, 0.9)
    ):
        """
        Show a toast notification.
        
        Args:
            message: Text to display
            duration: How long to show before fading
            color: Background color (default: green for success)
        """
        # Clean up existing toast
        self._cleanup()
        
        # Create label
        self._label = DirectLabel(
            parent=self.parent,
            text=message,
            text_scale=TextScale.LABEL,
            text_fg=(1, 1, 1, 1),
            text_align=0,  # Left align
            frameColor=color,
            pad=(0.02, 0.02),
            pos=(0, 0, -0.7),  # Bottom center area
            relief=DGG.FLAT
        )
        
        # Center the label based on text width
        bounds = self._label.getBounds()
        if bounds:
            width = (bounds[1] - bounds[0]) * TextScale.LABEL
            self._label.setX(-width / 2)
        
        # Start fully visible
        self._label.setColorScale(1, 1, 1, 1)
        
        # Animation sequence: wait, then fade out
        fade_duration = 0.5
        self._sequence = Sequence(
            Wait(duration),
            LerpColorScaleInterval(
                self._label,
                fade_duration,
                (1, 1, 1, 0),  # Fade to transparent
                (1, 1, 1, 1)   # From opaque
            ),
            Func(self._cleanup)
        )
        self._sequence.start()
        
    def show_success(self, message: str, duration: float = 2.0):
        """Show a success (green) toast."""
        self.show(message, duration, (0.2, 0.6, 0.2, 0.9))
        
    def show_error(self, message: str, duration: float = 3.0):
        """Show an error (red) toast."""
        self.show(message, duration, (0.6, 0.2, 0.2, 0.9))
        
    def show_info(self, message: str, duration: float = 2.0):
        """Show an info (blue) toast."""
        self.show(message, duration, (0.2, 0.3, 0.6, 0.9))
        
    def _cleanup(self):
        """Remove existing toast."""
        if self._sequence:
            self._sequence.pause()
            self._sequence = None
        if self._label:
            self._label.destroy()
            self._label = None
            
    def destroy(self):
        """Clean up resources."""
        self._cleanup()
