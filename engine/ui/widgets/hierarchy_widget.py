"""
Hierarchy widget for displaying scene graph or entity lists.
"""
from direct.gui.DirectGui import DirectFrame

class HierarchyWidget:
    """
    Tree view of the game world.
    
    Features:
    - Display Entity list
    - Parent/Child relationships
    - Selection handling
    """
    
    def __init__(self, parent_node):
        self.parent = parent_node
        self.items = []
        
    def refresh(self, world_root):
        """
        Rebuild tree from world data.
        
        Args:
            world_root: The root NodePath or ECS World to visualize.
        """
        # TODO: Traverse graph
        # TODO: Create UI buttons for nodes
        pass
        
    def on_selection_changed(self, callback):
        """TODO: Register selection listener."""
        pass
