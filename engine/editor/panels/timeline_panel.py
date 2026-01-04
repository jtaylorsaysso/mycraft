from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DirectSlider, DirectCheckButton, DGG
from panda3d.core import TextNode
from engine.editor.tools.common.timeline_widget import TimelineWidget
from engine.core.logger import get_logger

logger = get_logger(__name__)

class TimelinePanel:
    """Bottom panel with timeline and playback controls."""
    
    def __init__(self, parent, callbacks):
        self.callbacks = callbacks # play, pause, stop, capture, delete_key
        
        # Validate required callbacks
        required = ['play', 'pause', 'stop', 'capture', 'delete_key', 'looping']
        missing = [k for k in required if k not in callbacks or callbacks[k] is None]
        if missing:
            logger.warning(f"TimelinePanel missing callbacks: {missing}. Using no-op placeholders.")
            for key in missing:
                self.callbacks[key] = lambda *args: None
        
        # Main container (Bottom strip)
        self.frame = DirectFrame(
            parent=parent,
            frameColor=(0.1, 0.1, 0.1, 0.95),
            frameSize=(-2.0, 2.0, -0.4, 0.0), # Height 0.4
            pos=(0, 0, -1.0) # Aligned to bottom edge (screen -1)
        )
        # Shift up slightly so it's visible onscreen
        self.frame.setPos(0, 0, -0.6)
        
        self.timeline = None
        self.time_label = None
        
        self._build_ui()
        
    def _build_ui(self):
        # Controls Row
        y_controls = 0.3
        x_base = -1.2
        
        # Playback
        DirectButton(
            parent=self.frame, text=">", scale=0.05, pos=(x_base, 0, y_controls),
            command=self.callbacks.get('play')
        )
        DirectButton(
            parent=self.frame, text="||", scale=0.05, pos=(x_base+0.12, 0, y_controls),
            command=self.callbacks.get('pause')
        )
        DirectButton(
            parent=self.frame, text="[]", scale=0.05, pos=(x_base+0.24, 0, y_controls),
            command=self.callbacks.get('stop')
        )
        
        self.time_label = DirectLabel(
            parent=self.frame,
            text="0.0s",
            scale=0.04,
            pos=(x_base+0.45, 0, y_controls),
            text_fg=(1,1,1,1),
            frameColor=(0,0,0,0)
        )
        
        # Edit Tools
        x_tools = 0.5
        DirectButton(
            parent=self.frame, text="Capture Key", scale=0.04, pos=(x_tools, 0, y_controls),
            frameColor=(0.8, 0.6, 0.2, 1),
            command=self.callbacks.get('capture')
        )
        
        DirectButton(
            parent=self.frame, text="Delete Key", scale=0.04, pos=(x_tools+0.3, 0, y_controls),
            frameColor=(0.8, 0.3, 0.3, 1),
            command=self.callbacks.get('delete_key')
        )
        
        # Loop Checkbox
        self.loop_checkbox = DirectCheckButton(
            parent=self.frame,
            text="Loop",
            scale=0.04,
            pos=(1.2, 0, y_controls),
            text_fg=(0.8, 0.8, 0.8, 1),
            command=self.callbacks.get('looping')
        )

        # Timeline Widget
        self.timeline = TimelineWidget(
            parent=self.frame,
            x=-1.8, # Local coords in frame
            y=0.05,
            width=3.6,
            height=0.15,
            duration=1.0
        )
        
    def update_time(self, current, total):
        self.time_label['text'] = f"{current:.2f}s / {total:.2f}s"
        if self.timeline:
            self.timeline.set_playhead(current)
            
    def set_duration(self, duration):
        if self.timeline:
            self.timeline.set_duration(duration)
            
    def set_looping(self, state):
        self.loop_checkbox['indicatorValue'] = 1 if state else 0
        
    def cleanup(self):
        if self.timeline:
            self.timeline.destroy()
        self.frame.destroy()
