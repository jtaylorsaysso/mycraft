"""Animation editor for standalone suite.

Ported from engine/ui/animation_editor.py to work with EditorApp.
"""

from direct.gui.DirectGui import (
    DirectFrame, DirectLabel, DirectButton, DirectSlider,
    DirectOptionMenu, DGG, DirectCheckButton
)
from panda3d.core import TextNode, DSearchPath, Filename, Vec4
from pathlib import Path
from typing import Optional

from engine.editor.tools.common.timeline_widget import TimelineWidget
from engine.animation.core import AnimationClip, AnimationEvent
from engine.editor.selection import EditorSelection
from engine.core.logger import get_logger

logger = get_logger(__name__)


class AnimationEditor:
    """Standalone animation editor.
    
    Features:
    - Clip selection and playback
    - Timeline visualization
    - Parameter editing
    - Standalone integration
    """
    
    def __init__(self, app):
        """Initialize animation editor.
        
        Args:
            app: EditorApp instance
        """
        self.app = app
        self.registry = app.anim_registry
        
        # Shared selection
        self.selection: Optional[EditorSelection] = None
        
        # Playback state
        self.current_clip: Optional[AnimationClip] = None
        self.current_clip_name: Optional[str] = None
        self.playing = False
        self.current_time = 0.0
        
        # Colors (Dark Theme)
        self.bg_color = (0.08, 0.08, 0.08, 0.95)
        self.text_color = (0.9, 0.9, 0.9, 1)
        self.btn_color = (0.2, 0.6, 1.0, 1)
        self.accent_color = (0.2, 0.8, 0.2, 1)
        
        self.visible = False
        self.update_task = None
        
        # UI components
        self.main_frame: Optional[DirectFrame] = None
        self.clip_dropdown = None
        self.timeline = None
        self.time_label = None
        
        self._setup()
        self.hide()
        
    def set_selection(self, selection: EditorSelection):
        """Set shared selection state."""
        self.selection = selection
        
    def _setup(self):
        """Initialize UI components."""
        # Main Frame (offset from sidebar)
        self.main_frame = DirectFrame(
            parent=self.app.aspect2d,
            frameColor=(0, 0, 0, 0),
            frameSize=(-1.0, 1.4, -1.0, 1.0),
            pos=(0, 0, 0)
        )
        
        # Title
        DirectLabel(
            text="Animation Editor",
            scale=0.06,
            pos=(0.15, 0, 0.85),
            text_fg=self.text_color,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        self._build_clip_selector()
        self._build_playback_controls()
        self._build_timeline()
        self._build_parameter_panel()
        self._build_event_editor()
        self._build_footer()
        
    def show(self):
        """Show editor."""
        self.visible = True
        if self.main_frame:
            self.main_frame.show()
            
        # Refresh clip list
        self._refresh_clip_list()
        
        logger.debug("AnimationEditor shown")
            
    def hide(self):
        """Hide editor."""
        self.visible = False
        if self.main_frame:
            self.main_frame.hide()
            
        self._stop_playback()
        logger.debug("AnimationEditor hidden")
        
    def cleanup(self):
        """Clean up resources."""
        self.hide()
        if self.timeline:
            self.timeline.destroy()
        if self.main_frame:
            self.main_frame.destroy()
            
    # UI Building
    
    def _build_clip_selector(self):
        """Build clip selection dropdown."""
        DirectLabel(
            text="Clip:",
            scale=0.045,
            pos=(-0.8, 0, 0.7),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        self.clip_dropdown = DirectOptionMenu(
            items=["(no clips)"],
            scale=0.045,
            pos=(-0.5, 0, 0.7),
            initialitem=0,
            highlightColor=(0.3, 0.3, 0.3, 1),
            command=self._on_clip_selected,
            parent=self.main_frame
        )
        
    def _refresh_clip_list(self):
        """Refresh items in clip dropdown."""
        if not self.clip_dropdown:
            return
            
        clip_names = self.registry.list_clips()
        if not clip_names:
            clip_names = ["(no clips)"]
            
        # Update dropdown items
        self.clip_dropdown['items'] = clip_names
        
        # If current clip isn't selected, select first
        if self.current_clip_name in clip_names:
            self.clip_dropdown.set(self.current_clip_name)
        else:
            self.clip_dropdown.set(clip_names[0])
            self._on_clip_selected(clip_names[0])
            
    def _build_playback_controls(self):
        """Build playback controls."""
        y = 0.55
        x_base = -0.5
        spacing = 0.15
        
        # Play
        DirectButton(
            text="▶ Play",
            scale=0.045,
            pos=(x_base, 0, y),
            frameColor=self.btn_color,
            text_fg=(1, 1, 1, 1),
            command=self._on_play,
            parent=self.main_frame
        )
        
        # Pause
        DirectButton(
            text="⏸ Pause",
            scale=0.045,
            pos=(x_base + spacing, 0, y),
            frameColor=(0.5, 0.5, 0.5, 1),
            text_fg=(1, 1, 1, 1),
            command=self._on_pause,
            parent=self.main_frame
        )
        
        # Stop
        DirectButton(
            text="⏹ Stop",
            scale=0.045,
            pos=(x_base + spacing * 2, 0, y),
            frameColor=(0.6, 0.2, 0.2, 1),
            text_fg=(1, 1, 1, 1),
            command=self._on_stop,
            parent=self.main_frame
        )
        
        # Time display
        self.time_label = DirectLabel(
            text="0.00s / 0.00s",
            scale=0.045,
            pos=(x_base + spacing * 4, 0, y),
            text_fg=self.text_color,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
    def _build_timeline(self):
        """Build timeline widget."""
        DirectLabel(
            text="Timeline",
            scale=0.045,
            pos=(-0.8, 0, 0.35),
            text_fg=self.accent_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        self.timeline = TimelineWidget(
            parent=self.main_frame,
            x=-0.8,
            y=0.25,
            width=1.8,
            height=0.2,
            duration=1.0
        )
        
    def _build_parameter_panel(self):
        """Build parameter panel."""
        y = -0.1
        
        DirectLabel(
            text="Parameters",
            scale=0.045,
            pos=(-0.8, 0, y),
            text_fg=self.accent_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        y -= 0.12
        
        # Duration
        DirectLabel(
            text="Duration (s)",
            scale=0.04,
            pos=(-0.8, 0, y),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        self.duration_slider = DirectSlider(
            range=(0.1, 5.0),
            value=1.0,
            pageSize=0.5,
            scale=0.4,
            pos=(-0.2, 0, y),
            command=self._on_duration_changed,
            parent=self.main_frame
        )
        
        # Value label
        self.duration_val_label = DirectLabel(
            text="1.00",
            scale=0.04,
            pos=(0.3, 0, y),
            text_fg=self.text_color,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        y -= 0.1
        
        # Looping
        self.looping_checkbox = DirectCheckButton(
            text="Looping",
            scale=0.045,
            pos=(-0.8, 0, y),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            indicatorValue=1,
            boxBorder=0,
            boxRelief=DGG.FLAT,
            command=self._on_looping_changed,
            parent=self.main_frame
        )
        
    def _build_event_editor(self):
        """Build event panel stub."""
        y = -0.4
        
        DirectLabel(
            text="Events (Stub)",
            scale=0.045,
            pos=(-0.8, 0, y),
            text_fg=(0.5, 0.5, 0.5, 1),
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
    def _build_footer(self):
        """Build footer."""
        # Save button
        DirectButton(
            text="💾 Save Clip",
            scale=0.05,
            pos=(0.0, 0, -0.8),
            frameColor=self.btn_color,
            text_fg=(1, 1, 1, 1),
            command=self._on_save,
            parent=self.main_frame
        )
        
    # Logic
    
    def _on_clip_selected(self, clip_name: str):
        if clip_name == "(no clips)":
            return
        
        clip = self.registry.get_clip(clip_name)
        if not clip:
            return
            
        self.current_clip = clip
        self.current_clip_name = clip_name
        self._stop_playback()
        
        # Update UI
        self.duration_slider['value'] = clip.duration
        self.duration_val_label['text'] = f"{clip.duration:.2f}"
        self.looping_checkbox['indicatorValue'] = 1 if clip.looping else 0
        
        # Update timeline
        self.timeline.set_duration(clip.duration)
        self._refresh_timeline()
        self._update_time_display()
        
    def _refresh_timeline(self):
        if not self.timeline or not self.current_clip:
            return
            
        self.timeline.clear_markers()
        for kf in self.current_clip.keyframes:
            self.timeline.add_keyframe_marker(kf.time)
        for event in self.current_clip.events:
            self.timeline.add_event_marker(event.time, event.event_name)
            
    def _on_play(self):
        if not self.current_clip:
            return
        self.playing = True
        if not self.update_task:
            self.update_task = self.app.taskMgr.add(self._update_playback, "AnimEditorUpdate")
            
    def _on_pause(self):
        self.playing = False
        
    def _on_stop(self):
        self._stop_playback()
        self.current_time = 0.0
        if self.timeline:
            self.timeline.set_playhead(0.0)
        self._update_time_display()
        
    def _stop_playback(self):
        self.playing = False
        if self.update_task:
            self.app.taskMgr.remove(self.update_task)
            self.update_task = None
            
    def _update_playback(self, task):
        if not self.playing or not self.current_clip:
            return task.cont
            
        dt = globalClock.getDt()
        self.current_time += dt
        
        if self.current_clip.looping:
            self.current_time %= self.current_clip.duration
        elif self.current_time >= self.current_clip.duration:
            self.current_time = self.current_clip.duration
            self.playing = False
            
        if self.timeline:
            self.timeline.set_playhead(self.current_time)
        self._update_time_display()
        
        return task.cont
        
    def _update_time_display(self):
        if self.time_label and self.current_clip:
            self.time_label['text'] = f"{self.current_time:.2f}s / {self.current_clip.duration:.2f}s"
            
    def _on_duration_changed(self):
        if not self.current_clip:
            return
        val = self.duration_slider['value']
        self.current_clip.duration = val
        self.duration_val_label['text'] = f"{val:.2f}"
        if self.timeline:
            self.timeline.set_duration(val)
            
    def _on_looping_changed(self, value):
        if not self.current_clip:
            return
        self.current_clip.looping = bool(value)
        
    def _on_save(self):
        if not self.current_clip_name or not self.current_clip:
            return
        
        output_path = Path("data/animations") / f"{self.current_clip_name}.json"
        try:
            self.registry.save_to_json(self.current_clip_name, output_path)
            logger.info(f"Saved clip {self.current_clip_name}")
        except Exception as e:
            logger.error(f"Failed to save clip: {e}")
