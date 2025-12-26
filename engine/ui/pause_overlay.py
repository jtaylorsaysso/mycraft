"""Simple pause overlay for when game is paused."""

from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DGG
from panda3d.core import TextNode


class PauseOverlay:
    """Simple pause menu overlay."""
    
    def __init__(self, base, on_resume=None, on_quit=None):
        """Initialize pause overlay.
        
        Args:
            base: ShowBase instance
            on_resume: Callback when resume is clicked
            on_quit: Callback when quit is clicked
        """
        self.base = base
        self.on_resume = on_resume
        self.on_quit = on_quit
        self.visible = False
        
        # Semi-transparent background
        self.frame = DirectFrame(
            frameColor=(0, 0, 0, 0.7),
            frameSize=(-2, 2, -2, 2),
            pos=(0, 0, 0),
            parent=base.aspect2d,
            relief=DGG.FLAT
        )
        
        # Title
        DirectLabel(
            text="PAUSED",
            scale=0.15,
            pos=(0, 0, 0.5),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0),
            parent=self.frame
        )
        
        # Instructions
        DirectLabel(
            text="Press ESC to Resume",
            scale=0.06,
            pos=(0, 0, 0.2),
            text_fg=(0.8, 0.8, 0.8, 1),
            frameColor=(0, 0, 0, 0),
            parent=self.frame
        )
        
        # Resume button
        DirectButton(
            text="Resume (ESC)",
            scale=0.08,
            pos=(0, 0, -0.1),
            frameColor=(0.2, 0.6, 1.0, 1),
            text_fg=(1, 1, 1, 1),
            command=self._on_resume_clicked,
            parent=self.frame,
            relief=DGG.RAISED
        )
        
        # Quit button (if callback provided)
        if on_quit:
            DirectButton(
                text="Quit to Menu",
                scale=0.08,
                pos=(0, 0, -0.3),
                frameColor=(0.8, 0.2, 0.2, 1),
                text_fg=(1, 1, 1, 1),
                command=self._on_quit_clicked,
                parent=self.frame,
                relief=DGG.RAISED
            )
        
        self.frame.hide()
    
    def _on_resume_clicked(self):
        """Handle resume button click."""
        if self.on_resume:
            self.on_resume()
    
    def _on_quit_clicked(self):
        """Handle quit button click."""
        if self.on_quit:
            self.on_quit()
    
    def show(self):
        """Show the pause overlay."""
        self.visible = True
        self.frame.show()
    
    def hide(self):
        """Hide the pause overlay."""
        self.visible = False
        self.frame.hide()
    
    def toggle(self):
        """Toggle pause overlay visibility."""
        if self.visible:
            self.hide()
        else:
            self.show()
    
    def cleanup(self):
        """Clean up the overlay."""
        self.frame.destroy()
