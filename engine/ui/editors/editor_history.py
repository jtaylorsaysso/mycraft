"""
Undo/redo history stack for model editor operations.

Implements the Command pattern for reversible editor actions.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional
from engine.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EditorCommand:
    """Single undoable/redoable command.
    
    Attributes:
        execute: Function to execute the command
        undo: Function to reverse the command
        description: Human-readable description for debugging/UI
    """
    execute: Callable[[], None]
    undo: Callable[[], None]
    description: str


class EditorHistory:
    """Manages undo/redo stack for editor operations.
    
    Maintains two stacks:
    - undo_stack: Commands that can be undone
    - redo_stack: Commands that can be redone
    
    When a new command is executed, the redo stack is cleared.
    """
    
    def __init__(self, max_history: int = 50):
        """Initialize history manager.
        
        Args:
            max_history: Maximum number of commands to keep in history
        """
        self.max_history = max_history
        self.undo_stack: List[EditorCommand] = []
        self.redo_stack: List[EditorCommand] = []
        
    def execute(self, command: EditorCommand) -> None:
        """Execute a command and add it to the undo stack.
        
        Args:
            command: Command to execute
        """
        # Execute the command
        try:
            command.execute()
        except Exception as e:
            logger.error(f"Failed to execute command '{command.description}': {e}")
            return
            
        # Add to undo stack
        self.undo_stack.append(command)
        
        # Enforce max history limit
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
            
        # Clear redo stack (new action invalidates redo history)
        self.redo_stack.clear()
        
        logger.debug(f"Executed: {command.description}")
        
    def undo(self) -> bool:
        """Undo the last command.
        
        Returns:
            True if undo was successful, False if nothing to undo
        """
        if not self.can_undo():
            return False
            
        command = self.undo_stack.pop()
        
        try:
            command.undo()
            self.redo_stack.append(command)
            logger.debug(f"Undid: {command.description}")
            return True
        except Exception as e:
            logger.error(f"Failed to undo command '{command.description}': {e}")
            # Put command back on undo stack
            self.undo_stack.append(command)
            return False
            
    def redo(self) -> bool:
        """Redo the last undone command.
        
        Returns:
            True if redo was successful, False if nothing to redo
        """
        if not self.can_redo():
            return False
            
        command = self.redo_stack.pop()
        
        try:
            command.execute()
            self.undo_stack.append(command)
            logger.debug(f"Redid: {command.description}")
            return True
        except Exception as e:
            logger.error(f"Failed to redo command '{command.description}': {e}")
            # Put command back on redo stack
            self.redo_stack.append(command)
            return False
            
    def can_undo(self) -> bool:
        """Check if undo is available.
        
        Returns:
            True if there are commands to undo
        """
        return len(self.undo_stack) > 0
        
    def can_redo(self) -> bool:
        """Check if redo is available.
        
        Returns:
            True if there are commands to redo
        """
        return len(self.redo_stack) > 0
        
    def clear(self) -> None:
        """Clear all history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        logger.debug("History cleared")
        
    def get_undo_description(self) -> Optional[str]:
        """Get description of the next command that would be undone.
        
        Returns:
            Description string or None if nothing to undo
        """
        if self.can_undo():
            return self.undo_stack[-1].description
        return None
        
    def get_redo_description(self) -> Optional[str]:
        """Get description of the next command that would be redone.
        
        Returns:
            Description string or None if nothing to redo
        """
        if self.can_redo():
            return self.redo_stack[-1].description
        return None
        
    def get_history_count(self) -> int:
        """Get total number of commands in history.
        
        Returns:
            Number of commands that can be undone
        """
        return len(self.undo_stack)
