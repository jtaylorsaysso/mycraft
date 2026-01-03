"""
Tests for EditorHistory undo/redo stack.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ui.editors.editor_history import EditorHistory, EditorCommand


class TestEditorHistory(unittest.TestCase):
    def setUp(self):
        self.history = EditorHistory(max_history=10)
        self.counter = 0
        
    def test_initialization(self):
        """Test history initializes empty."""
        self.assertFalse(self.history.can_undo())
        self.assertFalse(self.history.can_redo())
        self.assertEqual(self.history.get_history_count(), 0)
        
    def test_execute_command(self):
        """Test executing a command."""
        executed = False
        
        def execute_fn():
            nonlocal executed
            executed = True
            
        def undo_fn():
            nonlocal executed
            executed = False
            
        cmd = EditorCommand(execute_fn, undo_fn, "Test command")
        self.history.execute(cmd)
        
        self.assertTrue(executed)
        self.assertTrue(self.history.can_undo())
        self.assertFalse(self.history.can_redo())
        self.assertEqual(self.history.get_history_count(), 1)
        
    def test_undo_command(self):
        """Test undoing a command."""
        value = 0
        
        def execute_fn():
            nonlocal value
            value = 10
            
        def undo_fn():
            nonlocal value
            value = 0
            
        cmd = EditorCommand(execute_fn, undo_fn, "Set value")
        self.history.execute(cmd)
        self.assertEqual(value, 10)
        
        success = self.history.undo()
        self.assertTrue(success)
        self.assertEqual(value, 0)
        self.assertFalse(self.history.can_undo())
        self.assertTrue(self.history.can_redo())
        
    def test_redo_command(self):
        """Test redoing a command."""
        value = 0
        
        def execute_fn():
            nonlocal value
            value = 10
            
        def undo_fn():
            nonlocal value
            value = 0
            
        cmd = EditorCommand(execute_fn, undo_fn, "Set value")
        self.history.execute(cmd)
        self.history.undo()
        
        success = self.history.redo()
        self.assertTrue(success)
        self.assertEqual(value, 10)
        self.assertTrue(self.history.can_undo())
        self.assertFalse(self.history.can_redo())
        
    def test_multiple_commands(self):
        """Test multiple commands in sequence."""
        values = []
        
        for i in range(3):
            def make_execute(val):
                return lambda: values.append(val)
            def make_undo():
                return lambda: values.pop()
                
            cmd = EditorCommand(make_execute(i), make_undo(), f"Add {i}")
            self.history.execute(cmd)
            
        self.assertEqual(values, [0, 1, 2])
        self.assertEqual(self.history.get_history_count(), 3)
        
        # Undo twice
        self.history.undo()
        self.history.undo()
        self.assertEqual(values, [0])
        
        # Redo once
        self.history.redo()
        self.assertEqual(values, [0, 1])
        
    def test_new_command_clears_redo(self):
        """Test that executing a new command clears redo stack."""
        value = 0
        
        def make_cmd(new_val, desc):
            def execute_fn():
                nonlocal value
                value = new_val
            def undo_fn():
                nonlocal value
                value = 0
            return EditorCommand(execute_fn, undo_fn, desc)
            
        self.history.execute(make_cmd(10, "Set 10"))
        self.history.undo()
        
        self.assertTrue(self.history.can_redo())
        
        # Execute new command
        self.history.execute(make_cmd(20, "Set 20"))
        
        # Redo should be cleared
        self.assertFalse(self.history.can_redo())
        
    def test_max_history_limit(self):
        """Test that history respects max limit."""
        history = EditorHistory(max_history=3)
        
        for i in range(5):
            cmd = EditorCommand(lambda: None, lambda: None, f"Command {i}")
            history.execute(cmd)
            
        # Should only keep last 3
        self.assertEqual(history.get_history_count(), 3)
        
    def test_clear_history(self):
        """Test clearing history."""
        cmd = EditorCommand(lambda: None, lambda: None, "Test")
        self.history.execute(cmd)
        
        self.history.clear()
        
        self.assertFalse(self.history.can_undo())
        self.assertFalse(self.history.can_redo())
        self.assertEqual(self.history.get_history_count(), 0)
        
    def test_get_descriptions(self):
        """Test getting command descriptions."""
        cmd1 = EditorCommand(lambda: None, lambda: None, "First")
        cmd2 = EditorCommand(lambda: None, lambda: None, "Second")
        
        self.history.execute(cmd1)
        self.history.execute(cmd2)
        
        self.assertEqual(self.history.get_undo_description(), "Second")
        
        self.history.undo()
        self.assertEqual(self.history.get_undo_description(), "First")
        self.assertEqual(self.history.get_redo_description(), "Second")
        
    def test_undo_when_empty(self):
        """Test undo returns False when nothing to undo."""
        success = self.history.undo()
        self.assertFalse(success)
        
    def test_redo_when_empty(self):
        """Test redo returns False when nothing to redo."""
        success = self.history.redo()
        self.assertFalse(success)


if __name__ == '__main__':
    unittest.main()
