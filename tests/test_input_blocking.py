"""Tests for input blocking stack functionality."""

import pytest
from engine.input.manager import InputManager


class TestInputBlocking:
    """Test input blocking stack behavior."""
    
    def test_input_blocking_stack(self):
        """Test that multiple blockers can stack and unstack correctly."""
        manager = InputManager()
        
        # Initially not blocked
        assert not manager.is_input_blocked
        
        # Add first blocker
        manager.block_input("chat")
        assert manager.is_input_blocked
        assert len(manager._blocking_reasons) == 1
        
        # Add second blocker
        manager.block_input("dialogue")
        assert manager.is_input_blocked
        assert len(manager._blocking_reasons) == 2
        
        # Remove first blocker - still blocked
        manager.unblock_input("chat")
        assert manager.is_input_blocked
        assert len(manager._blocking_reasons) == 1
        
        # Remove second blocker - now unblocked
        manager.unblock_input("dialogue")
        assert not manager.is_input_blocked
        assert len(manager._blocking_reasons) == 0
    
    def test_input_blocking_order_independence(self):
        """Test that unblocking order doesn't matter."""
        manager = InputManager()
        
        # Add multiple blockers
        manager.block_input("chat")
        manager.block_input("dialogue")
        manager.block_input("cutscene")
        assert len(manager._blocking_reasons) == 3
        
        # Remove in different order
        manager.unblock_input("dialogue")  # Remove middle one
        assert manager.is_input_blocked
        assert len(manager._blocking_reasons) == 2
        
        manager.unblock_input("cutscene")  # Remove last one
        assert manager.is_input_blocked
        assert len(manager._blocking_reasons) == 1
        
        manager.unblock_input("chat")  # Remove first one
        assert not manager.is_input_blocked
        assert len(manager._blocking_reasons) == 0
    
    def test_input_blocked_when_any_reason_present(self):
        """Test that input is blocked when at least one reason exists."""
        manager = InputManager()
        
        assert not manager.is_input_blocked
        
        manager.block_input("combat")
        assert manager.is_input_blocked
        
        # Adding duplicate reason should not double-add
        manager.block_input("combat")
        assert len(manager._blocking_reasons) == 1
        
        manager.unblock_input("combat")
        assert not manager.is_input_blocked
    
    def test_unblock_nonexistent_reason(self):
        """Test that unblocking a non-existent reason is safe."""
        manager = InputManager()
        
        manager.block_input("chat")
        assert manager.is_input_blocked
        
        # Try to unblock something that wasn't blocked
        manager.unblock_input("dialogue")
        
        # Should still be blocked by chat
        assert manager.is_input_blocked
        assert len(manager._blocking_reasons) == 1
        
        manager.unblock_input("chat")
        assert not manager.is_input_blocked
