"""Centralized keybinding definitions for MyCraft.

This module defines all input actions and their default key bindings.
Many actions are context-sensitive, meaning the same key performs different
actions based on the player's state (e.g., Space = Jump/Vault/Climb/Glide).

Design Philosophy:
- Minimize key count while maximizing movement vocabulary
- Context-sensitive controls reduce cognitive load
- Optimized for both keyboard/mouse and future controller support
"""

from enum import Enum, auto
from typing import Dict, Optional, Set


class InputAction(Enum):
    """All possible input actions in the game.
    
    Many actions share the same key but activate based on context:
    - Space: Jump → Vault (near ledge) → Climb (facing wall) → Wall-run → Glide
    - Shift: Slide (moving) → Dodge (combat) → Crouch (stationary) → Dive (water)
    - E: Grab ledge / Interact (context-sensitive)
    """
    
    # ===== Core Movement =====
    MOVE_FORWARD = auto()
    MOVE_BACK = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    JUMP = auto()  # Context: also vault when near ledge
    
    # ===== Traversal Mechanics (Vision: Movement First) =====
    SPRINT = auto()  # Hold to sprint, enables momentum-based movement
    SLIDE = auto()  # Context: slide when sprinting, crouch when stationary
    CLIMB = auto()  # Context: climb when facing climbable surface
    GRAB_LEDGE = auto()  # Context: grab ledge / general interact
    WALL_RUN = auto()  # Future: wall mechanics when near wall
    GLIDE = auto()  # Future: glide/descend when airborne
    
    # ===== Combat (Timing-based) =====
    ATTACK_PRIMARY = auto()  # Light attack
    ATTACK_HEAVY = auto()  # Heavy/charged attack
    DODGE = auto()  # Context: dodge roll in combat
    PARRY = auto()  # Future: timing-based parry/block
    
    # ===== Camera =====
    CAMERA_TOGGLE_MODE = auto()  # Toggle 1st/3rd person
    CAMERA_ZOOM_IN = auto()  # Scroll wheel up
    CAMERA_ZOOM_OUT = auto()  # Scroll wheel down
    CAMERA_RESET = auto()  # Reset to default position
    CAMERA_SHOULDER_SWAP = auto()  # Swap over-shoulder view (left/right)
    
    # ===== UI/System =====
    PAUSE_MENU = auto()  # Open pause menu (auto-unlocks cursor)
    DEBUG_OVERLAY = auto()  # Toggle debug info
    BUG_REPORT = auto()  # Open bug report overlay
    
    # ===== Utility =====
    INVENTORY = auto()  # Open inventory (future)
    GOD_MODE = auto()  # Debug: toggle god mode (fly/noclip)
    ADMIN_CONSOLE = auto()  # Debug: admin console for multiplayer


# Default key bindings
DEFAULT_BINDINGS: Dict[InputAction, str] = {
    # Core Movement
    InputAction.MOVE_FORWARD: 'w',
    InputAction.MOVE_BACK: 's',
    InputAction.MOVE_LEFT: 'a',
    InputAction.MOVE_RIGHT: 'd',
    InputAction.JUMP: 'space',  # Context: vault when near ledge
    
    # Traversal
    InputAction.SPRINT: 'control',  # Hold to sprint (momentum)
    InputAction.SLIDE: 'shift',  # Context: slide/crouch/dodge
    InputAction.CLIMB: 'space',  # Context: climb when facing climbable
    InputAction.GRAB_LEDGE: 'e',  # Context: grab ledge / interact
    InputAction.WALL_RUN: 'space',  # Future: context when near wall
    InputAction.GLIDE: 'space',  # Future: context when airborne
    
    # Combat
    InputAction.ATTACK_PRIMARY: 'mouse1',  # Left click
    # InputAction.ATTACK_HEAVY: 'mouse3',  # Disabled - conflicts with parry
    InputAction.DODGE: 'shift',  # Context: dodge in combat
    InputAction.PARRY: 'mouse3',  # Right click for parry
    
    # Camera
    InputAction.CAMERA_TOGGLE_MODE: 'v',
    InputAction.CAMERA_ZOOM_IN: 'wheel_up',
    InputAction.CAMERA_ZOOM_OUT: 'wheel_down',
    InputAction.CAMERA_RESET: 'c',
    InputAction.CAMERA_SHOULDER_SWAP: 'x',
    
    # UI/System (Cursor auto-managed by game state)
    InputAction.PAUSE_MENU: 'escape',
    InputAction.DEBUG_OVERLAY: 'f3',
    InputAction.BUG_REPORT: 'f1',
    
    # Utility
    InputAction.INVENTORY: 'i',
    InputAction.GOD_MODE: 'g',
    InputAction.ADMIN_CONSOLE: '`',
}


class KeyBindingManager:
    """Manages key bindings and provides action queries.
    
    This class allows runtime rebinding (future feature) and provides
    helper methods to check if an action is pressed.
    """
    
    def __init__(self, bindings: Optional[Dict[InputAction, str]] = None):
        """Initialize with default or custom bindings.
        
        Args:
            bindings: Optional custom bindings. Uses DEFAULT_BINDINGS if None.
        """
        self.bindings = bindings or DEFAULT_BINDINGS.copy()
        # Reverse lookup: key -> set of actions
        self._key_to_actions: Dict[str, Set[InputAction]] = {}
        self._rebuild_reverse_lookup()
    
    def _rebuild_reverse_lookup(self):
        """Rebuild the reverse lookup table (key -> actions)."""
        self._key_to_actions.clear()
        for action, key in self.bindings.items():
            if key not in self._key_to_actions:
                self._key_to_actions[key] = set()
            self._key_to_actions[key].add(action)
    
    def get_key(self, action: InputAction) -> Optional[str]:
        """Get the key bound to an action.
        
        Args:
            action: The input action to query
            
        Returns:
            The key string, or None if not bound
        """
        return self.bindings.get(action)
    
    def get_actions_for_key(self, key: str) -> Set[InputAction]:
        """Get all actions bound to a key.
        
        Multiple actions can share the same key (context-sensitive).
        
        Args:
            key: The key string to query
            
        Returns:
            Set of actions bound to this key
        """
        return self._key_to_actions.get(key, set())
    
    def rebind(self, action: InputAction, new_key: str):
        """Rebind an action to a new key.
        
        Args:
            action: The action to rebind
            new_key: The new key to bind to
        """
        self.bindings[action] = new_key
        self._rebuild_reverse_lookup()
    
    def reset_to_defaults(self):
        """Reset all bindings to defaults."""
        self.bindings = DEFAULT_BINDINGS.copy()
        self._rebuild_reverse_lookup()


# Context-sensitive key documentation
CONTEXT_SENSITIVE_KEYS = {
    'space': [
        ('Jump', 'Always available'),
        ('Vault', 'When near ledge (future)'),
        ('Climb', 'When facing climbable surface (future)'),
        ('Wall-run', 'When near wall (future)'),
        ('Glide', 'When airborne (future)'),
    ],
    'shift': [
        ('Slide', 'When sprinting'),
        ('Dodge', 'In combat (future)'),
        ('Crouch', 'When stationary'),
        ('Dive', 'When underwater (future)'),
    ],
    'e': [
        ('Grab Ledge', 'When near ledge (future)'),
        ('Interact', 'When near interactable object (future)'),
    ],
    'mouse2': [
        ('Heavy Attack', 'In combat (future)'),
        ('Parry', 'Timing window in combat (future)'),
    ],
}


def get_context_help(key: str) -> str:
    """Get human-readable help text for context-sensitive keys.
    
    Args:
        key: The key to get help for
        
    Returns:
        Formatted help text explaining all contexts for this key
    """
    if key not in CONTEXT_SENSITIVE_KEYS:
        return f"Key '{key}' is not context-sensitive"
    
    contexts = CONTEXT_SENSITIVE_KEYS[key]
    lines = [f"Key '{key}' performs different actions based on context:"]
    for action, condition in contexts:
        lines.append(f"  • {action}: {condition}")
    
    return '\n'.join(lines)
