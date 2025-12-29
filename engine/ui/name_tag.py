"""
3D Name Tag System for Players

Provides billboarded text labels that float above player heads,
always facing the camera for readability.
"""

from panda3d.core import TextNode, NodePath, Vec3, Vec4
from typing import Optional


class NameTag:
    """
    3D billboarded name tag that follows a player and always faces the camera.
    """
    
    def __init__(self, parent_node: NodePath, name: str, offset: Vec3 = Vec3(0, 0, 2.2)):
        """Initialize name tag.
        
        Args:
            parent_node: NodePath to attach the name tag to (usually player root)
            name: Player name to display
            offset: Position offset from parent (default: 2.2 units above)
        """
        self.parent_node = parent_node
        self.offset = offset
        
        # Create TextNode for 3D text
        self.text_node = TextNode('name_tag')
        self.text_node.setText(name)
        
        # Configure text appearance
        self.text_node.setAlign(TextNode.ACenter)
        self.text_node.setTextColor(1, 1, 1, 1)  # White
        self.text_node.setCardColor(0, 0, 0, 0.7)  # Semi-transparent black background
        self.text_node.setCardAsMargin(0.1, 0.1, 0.05, 0.05)  # Padding
        self.text_node.setCardDecal(True)  # Draw background
        
        # Set text scale (smaller for 3D world)
        self.text_node.setTextScale(0.15)
        
        # Create NodePath from TextNode
        self.node_path = parent_node.attachNewNode(self.text_node)
        self.node_path.setPos(offset)
        
        # Make it billboard (always face camera)
        self.node_path.setBillboardPointEye()
        
        # Set render order to draw on top
        self.node_path.setBin('fixed', 40)
        self.node_path.setDepthTest(False)
        self.node_path.setDepthWrite(False)
    
    def set_name(self, name: str):
        """Update the displayed name.
        
        Args:
            name: New name to display
        """
        self.text_node.setText(name)
    
    def set_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Change text color.
        
        Args:
            r: Red component (0-1)
            g: Green component (0-1)
            b: Blue component (0-1)
            a: Alpha component (0-1)
        """
        self.text_node.setTextColor(r, g, b, a)
    
    def show(self):
        """Make the name tag visible."""
        self.node_path.show()
    
    def hide(self):
        """Hide the name tag."""
        self.node_path.hide()
    
    def cleanup(self):
        """Remove the name tag from the scene."""
        self.node_path.removeNode()


def create_player_name_tag(parent_node: NodePath, name: str, 
                           color: Optional[tuple] = None) -> NameTag:
    """Convenience function to create a name tag for a player.
    
    Args:
        parent_node: Player's root NodePath
        name: Player name
        color: Optional RGB(A) tuple for text color
        
    Returns:
        NameTag instance
    """
    tag = NameTag(parent_node, name)
    
    if color:
        if len(color) == 3:
            tag.set_color(color[0], color[1], color[2])
        elif len(color) == 4:
            tag.set_color(color[0], color[1], color[2], color[3])
    
    return tag
