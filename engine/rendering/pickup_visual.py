"""
Pickup Visual.

Visual representation for pickup items (color swatches).
"""

from panda3d.core import NodePath, CardMaker, LColor, TransparencyAttrib
from engine.color.palette import ColorPalette
import math

class PickupVisual:
    """
    Visual wrapper for a pickup entity.
    Renders a floating, rotating cube.
    """
    
    def __init__(self, parent: NodePath, color_name: str):
        self.root = parent.attachNewNode("pickup_visual")
        self.color_name = color_name
        self.hover_time = 0.0
        
        # Create cube geometry
        self.model = self._create_cube()
        self.model.reparentTo(self.root)
        
        # Apply color
        color_def = ColorPalette.get_color(color_name)
        if color_def:
            r, g, b, a = color_def.rgba
            self.model.setColor(r, g, b, a)
            
        # Scale
        self.root.setScale(0.4)
        
        # Offset to float above ground
        self.base_height = 0.5
        self.root.setZ(self.base_height)
        
    def _create_cube(self) -> NodePath:
        """Create a simple cube using CardMaker."""
        cm = CardMaker('card')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5) 
        
        cube = NodePath("cube")
        
        # 6 faces
        faces = [
            (0, 0, 0.5, 0, -90, 0),   # Top
            (0, 0, -0.5, 0, 90, 0),   # Bottom
            (0, -0.5, 0, 0, 0, 0),    # Front
            (0, 0.5, 0, 180, 0, 0),   # Back
            (-0.5, 0, 0, -90, 0, 0),  # Left
            (0.5, 0, 0, 90, 0, 0),    # Right
        ]
        
        for x, y, z, h, p, r in faces:
            card = cube.attachNewNode(cm.generate())
            card.setPos(x, y, z)
            card.setHpr(h, p, r)
            
        # Add internal glow/transparency?
        cube.setTransparency(TransparencyAttrib.MAlpha)
        
        return cube
        
    def update(self, dt: float):
        """Animate the pickup."""
        self.hover_time += dt
        
        # Rotate
        self.root.setH(self.root.getH() + 90 * dt)
        
        # Bob
        bob = math.sin(self.hover_time * 2.0) * 0.1
        self.root.setZ(self.base_height + bob)
        
    def destroy(self):
        """Clean up."""
        if self.root:
            self.root.removeNode()
            self.root = None
