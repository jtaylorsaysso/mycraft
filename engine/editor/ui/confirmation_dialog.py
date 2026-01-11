"""
Confirmation dialog for editor actions.

Modal dialog with Yes/No/Cancel buttons for confirming destructive actions.
"""

from typing import Optional, Callable
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DGG
from panda3d.core import TextNode

from engine.editor.ui.theme import Colors, TextScale, Spacing
from engine.editor.ui.widgets import EditorButton


class ConfirmationDialog:
    """
    Modal confirmation dialog.
    
    Usage:
        dialog = ConfirmationDialog(aspect2d)
        dialog.show(
            "Discard unsaved changes?",
            on_yes=lambda: do_action(),
            on_no=lambda: cancel()
        )
    """
    
    def __init__(self, parent):
        """
        Initialize confirmation dialog.
        
        Args:
            parent: Parent GUI node (typically aspect2d)
        """
        self.parent = parent
        self._frame: Optional[DirectFrame] = None
        self._overlay: Optional[DirectFrame] = None
        self._on_yes: Optional[Callable] = None
        self._on_no: Optional[Callable] = None
        self._on_cancel: Optional[Callable] = None
        
    def show(
        self,
        message: str,
        on_yes: Optional[Callable] = None,
        on_no: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        yes_text: str = "Yes",
        no_text: str = "No",
        show_cancel: bool = False
    ):
        """
        Show confirmation dialog.
        
        Args:
            message: Message to display
            on_yes: Callback for Yes button
            on_no: Callback for No button
            on_cancel: Callback for Cancel button (only if show_cancel=True)
            yes_text: Text for Yes button
            no_text: Text for No button
            show_cancel: Whether to show Cancel button
        """
        self._cleanup()
        
        self._on_yes = on_yes
        self._on_no = on_no
        self._on_cancel = on_cancel
        
        # Semi-transparent overlay to block input
        self._overlay = DirectFrame(
            parent=self.parent,
            frameColor=(0, 0, 0, 0.5),
            frameSize=(-2, 2, -2, 2),
            pos=(0, 0, 0),
            sortOrder=100
        )
        
        # Dialog box
        dialog_width = 0.5
        dialog_height = 0.25
        self._frame = DirectFrame(
            parent=self._overlay,
            frameColor=(0.15, 0.15, 0.18, 0.98),
            frameSize=(-dialog_width, dialog_width, -dialog_height, dialog_height),
            pos=(0, 0, 0),
            relief=DGG.FLAT
        )
        
        # Message label
        DirectLabel(
            parent=self._frame,
            text=message,
            text_scale=TextScale.LABEL,
            text_fg=Colors.TEXT_PRIMARY,
            text_align=TextNode.ACenter,
            text_wordwrap=20,
            pos=(0, 0, 0.08),
            frameColor=(0, 0, 0, 0)
        )
        
        # Button row
        btn_y = -0.12
        btn_spacing = 0.18
        
        if show_cancel:
            # Three buttons: Yes | No | Cancel
            btn_x = -btn_spacing
        else:
            # Two buttons: Yes | No
            btn_x = -btn_spacing / 2
            
        # Yes button
        DirectButton(
            parent=self._frame,
            text=yes_text,
            text_scale=TextScale.BUTTON,
            text_fg=Colors.TEXT_PRIMARY,
            frameColor=Colors.ACCENT_SUCCESS,
            frameSize=(-0.08, 0.08, -0.03, 0.04),
            pos=(btn_x, 0, btn_y),
            command=self._handle_yes,
            relief=DGG.FLAT
        )
        btn_x += btn_spacing
        
        # No button
        DirectButton(
            parent=self._frame,
            text=no_text,
            text_scale=TextScale.BUTTON,
            text_fg=Colors.TEXT_PRIMARY,
            frameColor=Colors.ACCENT_DANGER,
            frameSize=(-0.08, 0.08, -0.03, 0.04),
            pos=(btn_x, 0, btn_y),
            command=self._handle_no,
            relief=DGG.FLAT
        )
        
        if show_cancel:
            btn_x += btn_spacing
            DirectButton(
                parent=self._frame,
                text="Cancel",
                text_scale=TextScale.BUTTON,
                text_fg=Colors.TEXT_PRIMARY,
                frameColor=Colors.BTN_DEFAULT,
                frameSize=(-0.08, 0.08, -0.03, 0.04),
                pos=(btn_x, 0, btn_y),
                command=self._handle_cancel,
                relief=DGG.FLAT
            )
            
    def _handle_yes(self):
        """Handle Yes button click."""
        callback = self._on_yes
        self._cleanup()
        if callback:
            callback()
            
    def _handle_no(self):
        """Handle No button click."""
        callback = self._on_no
        self._cleanup()
        if callback:
            callback()
            
    def _handle_cancel(self):
        """Handle Cancel button click."""
        callback = self._on_cancel
        self._cleanup()
        if callback:
            callback()
            
    def _cleanup(self):
        """Remove dialog elements."""
        if self._frame:
            self._frame.destroy()
            self._frame = None
        if self._overlay:
            self._overlay.destroy()
            self._overlay = None
        self._on_yes = None
        self._on_no = None
        self._on_cancel = None
        
    def hide(self):
        """Hide the dialog."""
        self._cleanup()
        
    def destroy(self):
        """Clean up resources."""
        self._cleanup()
