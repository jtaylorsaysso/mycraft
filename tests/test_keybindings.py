"""Tests for the keybindings system."""

import pytest
from engine.input.keybindings import (
    InputAction,
    DEFAULT_BINDINGS,
    KeyBindingManager,
    CONTEXT_SENSITIVE_KEYS,
    get_context_help
)


class TestInputAction:
    """Test InputAction enum."""
    
    def test_all_actions_exist(self):
        """Verify all expected actions are defined."""
        expected_actions = [
            'MOVE_FORWARD', 'MOVE_BACK', 'MOVE_LEFT', 'MOVE_RIGHT', 'JUMP',
            'SPRINT', 'SLIDE', 'CLIMB', 'GRAB_LEDGE', 'WALL_RUN', 'GLIDE',
            'ATTACK_PRIMARY', 'ATTACK_HEAVY', 'DODGE', 'PARRY',
            'CAMERA_TOGGLE_MODE', 'CAMERA_ZOOM_IN', 'CAMERA_ZOOM_OUT',
            'CAMERA_RESET', 'CAMERA_SHOULDER_SWAP',
            'PAUSE_MENU', 'DEBUG_OVERLAY', 'BUG_REPORT',
            'INVENTORY', 'GOD_MODE', 'ADMIN_CONSOLE'
        ]
        
        for action_name in expected_actions:
            assert hasattr(InputAction, action_name), f"Missing action: {action_name}"
    
    def test_actions_are_unique(self):
        """Verify all action values are unique."""
        values = [action.value for action in InputAction]
        assert len(values) == len(set(values)), "Duplicate action values found"


class TestDefaultBindings:
    """Test default key bindings."""
    
    def test_all_actions_have_bindings(self):
        """Verify every action has a default binding."""
        for action in InputAction:
            assert action in DEFAULT_BINDINGS, f"No binding for {action.name}"
    
    def test_core_movement_keys(self):
        """Verify core movement uses WASD."""
        assert DEFAULT_BINDINGS[InputAction.MOVE_FORWARD] == 'w'
        assert DEFAULT_BINDINGS[InputAction.MOVE_BACK] == 's'
        assert DEFAULT_BINDINGS[InputAction.MOVE_LEFT] == 'a'
        assert DEFAULT_BINDINGS[InputAction.MOVE_RIGHT] == 'd'
        assert DEFAULT_BINDINGS[InputAction.JUMP] == 'space'
    
    def test_traversal_keys(self):
        """Verify traversal mechanics use correct keys."""
        assert DEFAULT_BINDINGS[InputAction.SPRINT] == 'control'
        assert DEFAULT_BINDINGS[InputAction.SLIDE] == 'shift'
        assert DEFAULT_BINDINGS[InputAction.GRAB_LEDGE] == 'e'
    
    def test_camera_keys(self):
        """Verify camera controls."""
        assert DEFAULT_BINDINGS[InputAction.CAMERA_TOGGLE_MODE] == 'v'
        assert DEFAULT_BINDINGS[InputAction.CAMERA_RESET] == 'c'
        assert DEFAULT_BINDINGS[InputAction.CAMERA_SHOULDER_SWAP] == 'x'
    
    def test_system_keys(self):
        """Verify system keys."""
        assert DEFAULT_BINDINGS[InputAction.PAUSE_MENU] == 'escape'
        assert DEFAULT_BINDINGS[InputAction.DEBUG_OVERLAY] == 'f3'
        assert DEFAULT_BINDINGS[InputAction.BUG_REPORT] == 'f1'


class TestKeyBindingManager:
    """Test KeyBindingManager class."""
    
    def test_initialization_with_defaults(self):
        """Test manager initializes with default bindings."""
        manager = KeyBindingManager()
        assert manager.get_key(InputAction.MOVE_FORWARD) == 'w'
        assert manager.get_key(InputAction.PAUSE_MENU) == 'escape'
    
    def test_get_actions_for_key(self):
        """Test reverse lookup of actions by key."""
        manager = KeyBindingManager()
        
        # Space is context-sensitive (multiple actions)
        space_actions = manager.get_actions_for_key('space')
        assert InputAction.JUMP in space_actions
        assert InputAction.CLIMB in space_actions
        assert InputAction.WALL_RUN in space_actions
        assert InputAction.GLIDE in space_actions
    
    def test_rebind_action(self):
        """Test rebinding an action to a new key."""
        manager = KeyBindingManager()
        
        # Rebind jump to 'j'
        manager.rebind(InputAction.JUMP, 'j')
        assert manager.get_key(InputAction.JUMP) == 'j'
        
        # Verify reverse lookup updated
        j_actions = manager.get_actions_for_key('j')
        assert InputAction.JUMP in j_actions
    
    def test_reset_to_defaults(self):
        """Test resetting bindings to defaults."""
        manager = KeyBindingManager()
        
        # Rebind something
        manager.rebind(InputAction.JUMP, 'j')
        assert manager.get_key(InputAction.JUMP) == 'j'
        
        # Reset
        manager.reset_to_defaults()
        assert manager.get_key(InputAction.JUMP) == 'space'


class TestContextSensitiveKeys:
    """Test context-sensitive key documentation."""
    
    def test_space_is_context_sensitive(self):
        """Verify Space key has multiple contexts."""
        assert 'space' in CONTEXT_SENSITIVE_KEYS
        contexts = CONTEXT_SENSITIVE_KEYS['space']
        assert len(contexts) >= 4  # Jump, Vault, Climb, Wall-run, Glide
    
    def test_shift_is_context_sensitive(self):
        """Verify Shift key has multiple contexts."""
        assert 'shift' in CONTEXT_SENSITIVE_KEYS
        contexts = CONTEXT_SENSITIVE_KEYS['shift']
        assert len(contexts) >= 3  # Slide, Dodge, Crouch, Dive
    
    def test_get_context_help(self):
        """Test context help text generation."""
        help_text = get_context_help('space')
        assert 'Jump' in help_text
        assert 'Vault' in help_text
        assert 'context' in help_text.lower()
    
    def test_non_context_sensitive_key(self):
        """Test help for non-context-sensitive keys."""
        help_text = get_context_help('w')
        assert 'not context-sensitive' in help_text


class TestContextSensitiveDesign:
    """Test the context-sensitive design philosophy."""
    
    def test_space_multi_purpose(self):
        """Verify Space serves multiple traversal actions."""
        manager = KeyBindingManager()
        space_actions = manager.get_actions_for_key('space')
        
        # All these should use Space (context-dependent)
        traversal_actions = {
            InputAction.JUMP,
            InputAction.CLIMB,
            InputAction.WALL_RUN,
            InputAction.GLIDE
        }
        
        assert traversal_actions.issubset(space_actions)
    
    def test_shift_multi_purpose(self):
        """Verify Shift serves multiple contextual actions."""
        manager = KeyBindingManager()
        shift_actions = manager.get_actions_for_key('shift')
        
        # Slide and Dodge both use Shift
        assert InputAction.SLIDE in shift_actions
        assert InputAction.DODGE in shift_actions
