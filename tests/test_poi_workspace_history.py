"""
Tests for POI workspace undo/redo functionality.

Tests the EditorHistory command pattern in isolation.
"""

import pytest
from dataclasses import dataclass
from typing import Callable


# Inline the dataclass to test without Panda3D imports
@dataclass
class EditorCommand:
    """Single undoable/redoable command."""
    execute: Callable[[], None]
    undo: Callable[[], None]
    description: str


class EditorHistory:
    """Manages undo/redo stack for editor operations."""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.undo_stack = []
        self.redo_stack = []
        
    def execute(self, command):
        try:
            command.execute()
        except Exception:
            return
        self.undo_stack.append(command)
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        
    def undo(self):
        if not self.can_undo():
            return False
        command = self.undo_stack.pop()
        try:
            command.undo()
            self.redo_stack.append(command)
            return True
        except Exception:
            self.undo_stack.append(command)
            return False
            
    def redo(self):
        if not self.can_redo():
            return False
        command = self.redo_stack.pop()
        try:
            command.execute()
            self.undo_stack.append(command)
            return True
        except Exception:
            self.redo_stack.append(command)
            return False
            
    def can_undo(self):
        return len(self.undo_stack) > 0
        
    def can_redo(self):
        return len(self.redo_stack) > 0
        
    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
        
    def get_history_count(self):
        return len(self.undo_stack)
        
    def get_undo_description(self):
        return self.undo_stack[-1].description if self.can_undo() else None
        
    def get_redo_description(self):
        return self.redo_stack[-1].description if self.can_redo() else None


class TestEditorHistoryIntegration:
    """Tests for EditorHistory with EditorCommand pattern."""
    
    def test_execute_and_undo(self):
        """Verify execute adds to history and undo reverses it."""
        history = EditorHistory(max_history=50)
        
        # State tracker
        blocks = {}
        
        def add_block():
            blocks[(0, 0, 0)] = "stone"
            
        def remove_block():
            if (0, 0, 0) in blocks:
                del blocks[(0, 0, 0)]
                
        cmd = EditorCommand(
            execute=add_block,
            undo=remove_block,
            description="Place stone at (0,0,0)"
        )
        
        # Execute
        history.execute(cmd)
        assert (0, 0, 0) in blocks
        assert blocks[(0, 0, 0)] == "stone"
        assert history.can_undo()
        
        # Undo
        result = history.undo()
        assert result is True
        assert (0, 0, 0) not in blocks
        assert history.can_redo()
        
    def test_redo_restores_state(self):
        """Verify redo restores the executed state."""
        history = EditorHistory(max_history=50)
        
        blocks = {}
        
        cmd = EditorCommand(
            execute=lambda: blocks.update({(1, 2, 3): "dirt"}),
            undo=lambda: blocks.pop((1, 2, 3), None),
            description="Place dirt"
        )
        
        history.execute(cmd)
        history.undo()
        assert (1, 2, 3) not in blocks
        
        # Redo
        result = history.redo()
        assert result is True
        assert (1, 2, 3) in blocks
        
    def test_multiple_operations(self):
        """Verify multiple operations can be stacked and undone in order."""
        history = EditorHistory(max_history=50)
        
        blocks = {}
        
        # Add 3 blocks
        for i in range(3):
            pos = (i, 0, 0)
            cmd = EditorCommand(
                execute=lambda p=pos: blocks.update({p: "stone"}),
                undo=lambda p=pos: blocks.pop(p, None),
                description=f"Place at {pos}"
            )
            history.execute(cmd)
            
        assert len(blocks) == 3
        assert history.get_history_count() == 3
        
        # Undo all
        history.undo()
        assert len(blocks) == 2
        history.undo()
        assert len(blocks) == 1
        history.undo()
        assert len(blocks) == 0
        
    def test_clear_resets_history(self):
        """Verify clear removes all history."""
        history = EditorHistory()
        
        cmd = EditorCommand(
            execute=lambda: None,
            undo=lambda: None,
            description="Test"
        )
        history.execute(cmd)
        assert history.can_undo()
        
        history.clear()
        assert not history.can_undo()
        assert not history.can_redo()


class TestEditorCommandClosures:
    """Tests for closure behavior in EditorCommand."""
    
    def test_closure_captures_state(self):
        """
        Verify closures capture the correct state at command creation time.
        
        This is critical for undo/redo - the command must remember what
        block was at a position when the command was created, not what
        is there at undo time.
        """
        history = EditorHistory()
        
        blocks = {(5, 5, 5): "gold"}
        
        # Capture the block type before removal
        captured_pos = (5, 5, 5)
        captured_type = blocks.get(captured_pos, "stone")
        
        cmd = EditorCommand(
            execute=lambda: blocks.pop(captured_pos, None),
            undo=lambda: blocks.update({captured_pos: captured_type}),
            description="Remove gold block"
        )
        
        history.execute(cmd)
        assert captured_pos not in blocks
        
        # Undo should restore the gold block, not a default
        history.undo()
        assert blocks[captured_pos] == "gold"
