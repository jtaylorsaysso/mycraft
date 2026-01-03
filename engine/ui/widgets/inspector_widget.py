"""
Inspector widget for editing object properties.
"""
from direct.gui.DirectGui import DirectFrame

class InspectorWidget:
    """
    UI widget for inspecting and modifying object properties.
    
    Usage:
    - Inspect Entity components
    - Edit Brush settings
    - Tweak Global config
    """
    
    def __init__(self, parent_node):
        self.parent = parent_node
        self.target = None
        
    def inspect(self, target_object):
        """
        Bind the inspector to a target object.
        
        TODO: Use reflection (dir(), getattr()) to find editable fields.
        TODO: Clear previous UI.
        TODO: Generate input fields for int, float, str, bool, Color.
        """
        self.target = target_object
        self._refresh_ui()
        
    def _refresh_ui(self):
        """TODO: Rebuild UI based on target properties."""
        pass
        
    def _on_value_changed(self, field_name, new_value):
        """TODO: specific field update logic."""
        if self.target:
            setattr(self.target, field_name, new_value)
