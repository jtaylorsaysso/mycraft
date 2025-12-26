from typing import Dict, Set, Callable, Optional
from panda3d.core import WindowProperties, ModifierButtons
from engine.input.keybindings import InputAction, KeyBindingManager


class InputManager:
    """Manages keyboard and mouse input for Panda3D applications."""
    
    def __init__(self, base=None, key_bindings=None):
        """Initialize the input manager.
        
        Args:
            base: ShowBase instance (optional, can be passed later to setup)
            key_bindings: Optional KeyBindingManager instance
        """
        self.base = base
        self.keys_down: Set[str] = set()
        self.mouse_locked = False
        self.mouse_delta = (0.0, 0.0)
        self._last_mouse_pos = None
        self.key_bindings = key_bindings or KeyBindingManager()
        
        if self.base:
            self.setup(self.base)
            
    def setup(self, base):
        """Setup event listeners on the ShowBase instance."""
        print(f"🔌 InputManager.setup called with base: {base}")
        self.base = base
        # Accept all key events
        self.base.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        self.base.accept('keystroke', self._on_keystroke)
        
        # Also accept specific common keys for down/up tracking
        common_keys = [
            'w', 's', 'a', 'd', 'space', 'shift', 'control', 'escape', 
            'e', 'q', 'tab', 't', '/', 'g', 'enter', 'backspace', 'v'  # Added 'v' for camera toggle
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
        # Check event-based tracking first
        if key.lower() in self.keys_down:
            return True
            
        # Fallback: Poll Panda3D directly (more robust)
        if self.base and self.base.mouseWatcherNode.hasMouse():
            from panda3d.core import KeyboardButton
            # DEBUG: Check specifically for escape
            if key == 'escape':
                try:
                    state = self.base.mouseWatcherNode.is_button_down(KeyboardButton.escape())
                    print(f"DEBUG: Poll escape state: {state}")
                    return state
                except:
                    return False
                    
            try:
                # Handle single characters
                if len(key) == 1:
                    p3d_key = KeyboardButton.ascii_key(key.lower())
                    return self.base.mouseWatcherNode.is_button_down(p3d_key)
                
                # Handle special keys
                if key == 'escape':
                    return self.base.mouseWatcherNode.is_button_down(KeyboardButton.escape())
                elif key == 'space':
                    return self.base.mouseWatcherNode.is_button_down(KeyboardButton.space())
                elif key == 'shift':
                    return self.base.mouseWatcherNode.is_button_down(KeyboardButton.shift())
                elif key == 'control':
                    return self.base.mouseWatcherNode.is_button_down(KeyboardButton.control())
                elif key == 'enter':
                    return self.base.mouseWatcherNode.is_button_down(KeyboardButton.enter())
            except Exception:
                pass
                
        return False

    def is_action_active(self, action: InputAction) -> bool:
        """Check if an action is currently active (key held down).
        
        Args:
            action: The InputAction to check
            
        Returns:
            True if the bound key is pressed
        """
        key = self.key_bindings.get_key(action)
        if not key:
            return False
        return self.is_key_down(key)
    
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
            # Manual centered locking: reliable across platforms
            # 1. Get window size and center
            win_width = self.base.win.getXSize()
            win_height = self.base.win.getYSize()
            center_x = win_width // 2
            center_y = win_height // 2
            
            # 2. Get current mouse position (pixels)
            md = self.base.win.getPointer(0)
            current_x = md.getX()
            current_y = md.getY()
            
            # 3. Calculate delta
            dx_pixels = current_x - center_x
            dy_pixels = current_y - center_y
            
            # 4. Normalize delta to reasonable range (similar to getMouseX range of -1 to 1)
            # Assuming 1.0 corresponds to half-screen width
            self.mouse_delta = (
                (dx_pixels / win_width) * 2.0, 
                (dy_pixels / win_height) * 2.0
            )
            
            # 5. Re-center mouse if it moved
            if dx_pixels != 0 or dy_pixels != 0:
                self.base.win.movePointer(0, center_x, center_y)
                
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
