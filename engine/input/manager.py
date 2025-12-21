"""Panda3D Input Manager for keyboard and mouse handling."""

from typing import Dict, Set, Callable, Optional
from panda3d.core import WindowProperties, ModifierButtons


class InputManager:
    """Manages keyboard and mouse input for Panda3D applications."""
    
    def __init__(self, base=None):
        """Initialize the input manager.
        
        Args:
            base: ShowBase instance (optional, can be passed later to setup)
        """
        self.base = base
        self.keys_down: Set[str] = set()
        self.mouse_locked = False
        self.mouse_delta = (0.0, 0.0)
        self._last_mouse_pos = None
        
        if self.base:
            self.setup(self.base)
            
    def setup(self, base):
        """Setup event listeners on the ShowBase instance."""
        self.base = base
        # Accept all key events
        self.base.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        self.base.accept('keystroke', self._on_keystroke)
        
        # Also accept specific common keys for down/up tracking
        common_keys = [
            'w', 's', 'a', 'd', 'space', 'shift', 'control', 'escape', 
            'e', 'q', 'tab', 't', '/', 'g', 'enter', 'backspace'
        ]
        # Function keys
        for i in range(1, 13):
            common_keys.append(f'f{i}')
            
        # Mouse buttons
        common_keys.extend(['mouse1', 'mouse2', 'mouse3'])
        
        for key in common_keys:
            self.base.accept(key, self._on_key_down, [key])
            self.base.accept(f'{key}-up', self._on_key_up, [key])

    def _on_keystroke(self, key):
        """Handle arbitrary keystrokes."""
        pass # Optional logging

    def _on_key_down(self, key: str):
        self.keys_down.add(key)
    
    def _on_key_up(self, key: str):
        self.keys_down.discard(key)
    
    def is_key_down(self, key: str) -> bool:
        return key.lower() in self.keys_down
    
    def lock_mouse(self):
        if not self.base: return
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        self.base.win.requestProperties(props)
        self.mouse_locked = True
    
    def unlock_mouse(self):
        if not self.base: return
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self.base.win.requestProperties(props)
        self.mouse_locked = False
    
    def update(self):
        """Update mouse delta tracking."""
        if self.mouse_locked and self.base and self.base.mouseWatcherNode.hasMouse():
            mx = self.base.mouseWatcherNode.getMouseX()
            my = self.base.mouseWatcherNode.getMouseY()
            
            # In relative mode, Panda3D centers the mouse, but we can track the delta directly from mouseWatcherNode
            # Or if using M_relative, GetMouseX/Y returns the accumulated delta since last frame often?
            # Actually, Panda3D M_relative mode resets mouse to center. 
            # The getMouseX/Y returns coordinates from -1 to 1.
            
            self.mouse_delta = (mx, my)
            # Re-center is handled by M_relative
        else:
            self.mouse_delta = (0.0, 0.0)


class KeyBindings:
    FORWARD = 'w'
    BACK = 's'
    LEFT = 'a'
    RIGHT = 'd'
    JUMP = 'space'
    CROUCH = 'shift'
    ESCAPE = 'escape'
