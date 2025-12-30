"""Timeline widget for animation editor.

Custom DirectGUI widget for visualizing animation timelines with
keyframes, events, and playhead scrubbing.
"""

from direct.gui.DirectGui import DirectFrame, DirectLabel
from panda3d.core import LineSegs, NodePath, Vec4, TextNode
from typing import List, Tuple, Optional, Callable


class TimelineWidget:
    """Visual timeline for animation editing.
    
    Displays:
    - Time ruler with tick marks
    - Keyframe markers
    - Event markers
    - Playhead scrubber
    """
    
    def __init__(
        self,
        parent: NodePath,
        x: float,
        y: float,
        width: float,
        height: float,
        duration: float
    ):
        """Initialize timeline widget.
        
        Args:
            parent: Parent NodePath for UI
            x: X position (normalized screen coords)
            y: Y position (normalized screen coords)
            width: Width (normalized)
            height: Height (normalized)
            duration: Animation duration in seconds
        """
        self.parent = parent
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.duration = duration
        self.playhead_time = 0.0
        
        # Colors
        self.bg_color = Vec4(0.15, 0.15, 0.15, 1.0)
        self.ruler_color = Vec4(0.4, 0.4, 0.4, 1.0)
        self.keyframe_color = Vec4(0.2, 0.8, 0.2, 1.0)
        self.event_color = Vec4(0.8, 0.4, 0.2, 1.0)
        self.playhead_color = Vec4(1.0, 0.2, 0.2, 1.0)
        
        # Callbacks
        self.on_scrub: Optional[Callable[[float], None]] = None
        
        # Build UI
        self._create_background()
        self._create_ruler()
        
        # Storage for markers
        self.keyframe_markers: List[NodePath] = []
        self.event_markers: List[Tuple[NodePath, NodePath]] = []  # (line, label)
        self.playhead_node: Optional[NodePath] = None
        
        self._create_playhead()
        
    def _create_background(self):
        """Create timeline background."""
        self.background = DirectFrame(
            frameColor=(self.bg_color.x, self.bg_color.y, self.bg_color.z, self.bg_color.w),
            frameSize=(0, self.width, -self.height, 0),
            pos=(self.x, 0, self.y),
            parent=self.parent
        )
        
    def _create_ruler(self):
        """Create time ruler with tick marks."""
        # Ruler line
        segs = LineSegs()
        segs.setColor(self.ruler_color)
        segs.setThickness(2)
        
        # Main horizontal line
        segs.moveTo(0, 0, -self.height * 0.5)
        segs.drawTo(self.width, 0, -self.height * 0.5)
        
        # Tick marks every 0.1 seconds
        tick_interval = 0.1
        num_ticks = int(self.duration / tick_interval) + 1
        
        for i in range(num_ticks):
            time = i * tick_interval
            x = (time / self.duration) * self.width
            
            # Major tick every 0.5s, minor otherwise
            if i % 5 == 0:
                tick_height = self.height * 0.3
                # Add time label
                label = DirectLabel(
                    text=f\"{time:.1f}s\",
                    scale=0.03,
                    pos=(x, 0, -self.height * 0.5 - 0.05),
                    text_fg=(0.7, 0.7, 0.7, 1),
                    text_align=TextNode.ACenter,
                    frameColor=(0, 0, 0, 0),
                    parent=self.background
                )
            else:
                tick_height = self.height * 0.15
            
            segs.moveTo(x, 0, -self.height * 0.5)
            segs.drawTo(x, 0, -self.height * 0.5 + tick_height)
        
        self.ruler_node = self.background.attachNewNode(segs.create())
        
    def _create_playhead(self):
        """Create playhead scrubber."""
        segs = LineSegs()
        segs.setColor(self.playhead_color)
        segs.setThickness(3)
        
        # Vertical line
        segs.moveTo(0, 0, 0)
        segs.drawTo(0, 0, -self.height)
        
        self.playhead_node = self.background.attachNewNode(segs.create())
        self.set_playhead(0.0)
        
    def add_keyframe_marker(self, time: float, bone: str = ""):
        """Add a keyframe marker to the timeline.
        
        Args:
            time: Keyframe time in seconds
            bone: Bone name (optional, for tooltip)
        """
        x = (time / self.duration) * self.width
        
        # Create diamond marker
        segs = LineSegs()
        segs.setColor(self.keyframe_color)
        segs.setThickness(2)
        
        size = 0.015
        # Diamond shape
        segs.moveTo(x, 0, -self.height * 0.2)
        segs.drawTo(x + size, 0, -self.height * 0.3)
        segs.drawTo(x, 0, -self.height * 0.4)
        segs.drawTo(x - size, 0, -self.height * 0.3)
        segs.drawTo(x, 0, -self.height * 0.2)
        
        marker = self.background.attachNewNode(segs.create())
        self.keyframe_markers.append(marker)
        
    def add_event_marker(self, time: float, event_name: str, color: Optional[Vec4] = None):
        """Add an event marker to the timeline.
        
        Args:
            time: Event time in seconds
            event_name: Event name for label
            color: Optional custom color
        """
        x = (time / self.duration) * self.width
        marker_color = color if color else self.event_color
        
        # Create vertical line
        segs = LineSegs()
        segs.setColor(marker_color)
        segs.setThickness(2)
        segs.moveTo(x, 0, -self.height * 0.6)
        segs.drawTo(x, 0, -self.height * 0.9)
        
        line = self.background.attachNewNode(segs.create())
        
        # Create label
        label = DirectLabel(
            text=event_name,
            scale=0.025,
            pos=(x, 0, -self.height * 0.95),
            text_fg=(marker_color.x, marker_color.y, marker_color.z, 1),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            parent=self.background
        )
        
        self.event_markers.append((line, label))
        
    def set_playhead(self, time: float):
        """Set playhead position.
        
        Args:
            time: Time in seconds
        """
        self.playhead_time = max(0.0, min(time, self.duration))
        x = (self.playhead_time / self.duration) * self.width
        
        if self.playhead_node:
            self.playhead_node.setX(x)
            
    def clear_markers(self):
        """Clear all keyframe and event markers."""
        for marker in self.keyframe_markers:
            marker.removeNode()
        self.keyframe_markers.clear()
        
        for line, label in self.event_markers:
            line.removeNode()
            label.destroy()
        self.event_markers.clear()
        
    def set_duration(self, duration: float):
        """Update timeline duration and rebuild ruler.
        
        Args:
            duration: New duration in seconds
        """
        self.duration = duration
        
        # Rebuild ruler
        if hasattr(self, 'ruler_node'):
            self.ruler_node.removeNode()
        self._create_ruler()
        
        # Update playhead position
        self.set_playhead(self.playhead_time)
        
    def destroy(self):
        """Clean up widget resources."""
        self.clear_markers()
        if self.playhead_node:
            self.playhead_node.removeNode()
        if hasattr(self, 'ruler_node'):
            self.ruler_node.removeNode()
        self.background.destroy()
