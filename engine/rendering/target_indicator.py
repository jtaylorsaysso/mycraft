"""Target lock visual indicator."""

from panda3d.core import NodePath, CardMaker, TransparencyAttrib, LVector3f, LVector4f
import math


class TargetIndicator:
    """Visual ring indicator for locked targets.
    
    Displays a pulsing ring above locked entities to provide clear
    visual feedback for the targeting system.
    """
    
    def __init__(self, render: NodePath):
        """Initialize target indicator.
        
        Args:
            render: Panda3D render node to attach to
        """
        self.render = render
        self.root = render.attachNewNode("target_indicator")
        
        # Animation state
        self.pulse_time = 0.0
        self.base_scale = 1.5  # Ring radius
        
        # Create ring geometry
        self._create_ring()
        
        # Start hidden
        self.root.hide()
        
    def _create_ring(self):
        """Create billboard ring geometry."""
        # Create a simple quad for the ring
        cm = CardMaker('target_ring')
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)  # Centered quad
        
        ring_node = self.root.attachNewNode(cm.generate())
        
        # Make it billboard (always face camera)
        ring_node.setBillboardPointEye()
        
        # Enable transparency
        ring_node.setTransparency(TransparencyAttrib.MAlpha)
        
        # Default white color (will be tinted via setColorScale)
        # For now, using a solid color. Could load a ring texture later.
        # To make it look like a ring, we'll use a simple approach:
        # - Set a semi-transparent bright color with darker center
        # - Use color scaling to make edges brighter
        
        # Store reference
        self.ring_node = ring_node
        
        # Set initial scale
        ring_node.setScale(self.base_scale)
        
    def show(self, position: LVector3f, color: LVector4f = LVector4f(1.0, 0.2, 0.2, 0.8)):
        """Show indicator at position with color.
        
        Args:
            position: World position to place indicator
            color: RGBA color for the ring (default: red)
        """
        # Position slightly above target (at head height)
        offset_pos = position + LVector3f(0, 0, 2.0)
        self.root.setPos(offset_pos)
        
        # Set color
        self.ring_node.setColorScale(color)
        
        # Reset pulse animation
        self.pulse_time = 0.0
        
        # Show
        self.root.show()
        
    def hide(self):
        """Hide the indicator."""
        self.root.hide()
        
    def update(self, dt: float, position: LVector3f):
        """Update indicator position and animation.
        
        Args:
            dt: Delta time
            position: Target position to follow
        """
        if self.root.isHidden():
            return
            
        # Update position to follow target
        offset_pos = position + LVector3f(0, 0, 2.0)
        self.root.setPos(offset_pos)
        
        # Update pulse animation
        self.pulse_time += dt
        pulse_scale = 1.0 + 0.15 * math.sin(self.pulse_time * 3.0)
        self.ring_node.setScale(self.base_scale * pulse_scale)
        
    def cleanup(self):
        """Remove indicator from scene."""
        if self.root:
            self.root.removeNode()
            self.root = None
