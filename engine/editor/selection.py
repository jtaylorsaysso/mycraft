"""
Shared selection state for editor tools.

Provides a central store for selections that can be shared across editors.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, List
from engine.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EditorSelection:
    """Shared selection state across editors.
    
    Observers are notified when selection changes.
    """
    _selected_bone: Optional[str] = None
    _observers: List[Callable[[str, any], None]] = field(default_factory=list)
    
    @property
    def bone(self) -> Optional[str]:
        """Currently selected bone name."""
        return self._selected_bone
        
    @bone.setter
    def bone(self, value: Optional[str]):
        if value != self._selected_bone:
            self._selected_bone = value
            self._notify("bone", value)
            
    def add_observer(self, callback: Callable[[str, any], None]):
        """Add observer for selection changes.
        
        Args:
            callback: Function(property_name, new_value) called on change
        """
        self._observers.append(callback)
        
    def remove_observer(self, callback: Callable):
        """Remove an observer."""
        if callback in self._observers:
            self._observers.remove(callback)
            
    def _notify(self, prop: str, value):
        """Notify all observers of a change."""
        for observer in self._observers:
            try:
                observer(prop, value)
            except Exception as e:
                logger.error(f"Selection observer error: {e}")
