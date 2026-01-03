"""Animation editor window for visual animation editing.

Provides a separate DirectGUI window for editing animation clips with:
- Clip selection and playback controls
- Timeline visualization with scrubbing
- Parameter editing (duration, events, timing)
- Live preview with isolated mannequin
"""

from direct.gui.DirectGui import (
    DirectFrame, DirectLabel, DirectButton, DirectSlider,
    DirectOptionMenu, DGG, DirectEntry, DirectCheckButton
)
from panda3d.core import TextNode, Vec4, NodePath
from pathlib import Path
from typing import Optional

from engine.ui.base_editor import BaseEditorWindow
from engine.ui.timeline_widget import TimelineWidget
from engine.animation.animation_registry import AnimationRegistry
from engine.animation.core import AnimationClip, AnimationEvent
from engine.animation.combat import CombatClip


class AnimationEditorWindow(BaseEditorWindow):
    """In-engine animation editor with visual feedback.
    
    Features:
    - Clip selection dropdown
    - Playback controls (play/pause/stop/step)
    - Timeline scrubber with keyframe/event markers
    - Parameter sliders (duration, event timing)
    - Save/load to JSON
    """
    
    def __init__(self, base, registry: AnimationRegistry):
        """Initialize animation editor.
        
        Args:
            base: Panda3D ShowBase instance
            registry: AnimationRegistry for clip management
        """
        self.registry = registry
        
        # Playback state
        self.current_clip: Optional[AnimationClip] = None
        self.current_clip_name: Optional[str] = None
        self.playing = False
        self.current_time = 0.0
        
        # Colors (Dark Theme)
        self.bg_color = (0.08, 0.08, 0.08, 0.95)
        self.panel_color = (0.12, 0.12, 0.12, 1)
        self.text_color = (0.9, 0.9, 0.9, 1)
        self.btn_color = (0.2, 0.6, 1.0, 1)
        self.accent_color = (0.2, 0.8, 0.2, 1)
        
        # Task for updating playback
        self.update_task = None

        # Initialize base editor (calls setup())
        super().__init__(base, "Animation Editor")
        
    def setup(self):
        """Initialize UI components."""
        # Main Frame (larger than settings overlay)
        self.main_frame = DirectFrame(
            frameColor=self.bg_color,
            frameSize=(-1.2, 1.2, -0.85, 0.85),
            pos=(0, 0, 0),
            parent=self.ui_root,
            relief=DGG.FLAT
        )
        
        # Title
        DirectLabel(
            text="ANIMATION EDITOR",
            scale=0.08,
            pos=(0, 0, 0.75),
            text_fg=self.text_color,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        # Build UI sections
        self._build_clip_selector()
        self._build_playback_controls()
        self._build_timeline()
        self._build_parameter_panel()
        self._build_event_editor()
        self._build_footer()
        
    def show(self):
        """Show editor window and refresh state."""
        super().show()
        
        # Refresh clip list
        clip_names = self.registry.list_clips()
        if clip_names and hasattr(self, 'clip_dropdown'):
            self.clip_dropdown['items'] = clip_names

    def hide(self):
        """Hide editor window and stop playback."""
        super().hide()
        self.playing = False
        
        # Stop update task
        if self.update_task:
            self.base.taskMgr.remove(self.update_task)
            self.update_task = None

    def cleanup(self):
        """Clean up resources."""
        self.hide()
        if hasattr(self, 'timeline'):
            self.timeline.destroy()
        super().cleanup()

    # UI Building Methods (Adapted to use self.main_frame)
        
    def _build_clip_selector(self):
        """Build clip selection dropdown."""
        DirectLabel(
            text="Clip:",
            scale=0.05,
            pos=(-1.0, 0, 0.6),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        # Get clip names from registry
        clip_names = self.registry.list_clips()
        if not clip_names:
            clip_names = ["(no clips)"]
        
        self.clip_dropdown = DirectOptionMenu(
            items=clip_names,
            scale=0.05,
            pos=(-0.7, 0, 0.6),
            initialitem=0,
            highlightColor=(0.3, 0.3, 0.3, 1),
            command=self._on_clip_selected,
            parent=self.main_frame
        )
        
    def _build_playback_controls(self):
        """Build play/pause/stop/step buttons."""
        y = 0.45
        spacing = 0.15
        
        # Play button
        self.play_btn = DirectButton(
            text="▶ Play",
            scale=0.05,
            pos=(-0.6, 0, y),
            frameColor=self.btn_color,
            text_fg=(1, 1, 1, 1),
            command=self._on_play,
            parent=self.main_frame,
            relief=DGG.RAISED
        )
        
        # Pause button
        self.pause_btn = DirectButton(
            text="⏸ Pause",
            scale=0.05,
            pos=(-0.6 + spacing, 0, y),
            frameColor=(0.5, 0.5, 0.5, 1),
            text_fg=(1, 1, 1, 1),
            command=self._on_pause,
            parent=self.main_frame,
            relief=DGG.RAISED
        )
        
        # Stop button
        DirectButton(
            text="⏹ Stop",
            scale=0.05,
            pos=(-0.6 + spacing * 2, 0, y),
            frameColor=(0.6, 0.2, 0.2, 1),
            text_fg=(1, 1, 1, 1),
            command=self._on_stop,
            parent=self.main_frame,
            relief=DGG.RAISED
        )
        
        # Step backward
        DirectButton(
            text="◀",
            scale=0.04,
            pos=(-0.6 + spacing * 3, 0, y),
            frameColor=(0.4, 0.4, 0.4, 1),
            text_fg=(1, 1, 1, 1),
            command=lambda: self._step_frame(-0.016),  # ~1 frame at 60fps
            parent=self.main_frame,
            relief=DGG.RAISED
        )
        
        # Step forward
        DirectButton(
            text="▶",
            scale=0.04,
            pos=(-0.6 + spacing * 3 + 0.1, 0, y),
            frameColor=(0.4, 0.4, 0.4, 1),
            text_fg=(1, 1, 1, 1),
            command=lambda: self._step_frame(0.016),
            parent=self.main_frame,
            relief=DGG.RAISED
        )
        
        # Time display
        self.time_label = DirectLabel(
            text="0.00s / 0.00s",
            scale=0.045,
            pos=(0.3, 0, y),
            text_fg=self.text_color,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
    def _build_timeline(self):
        """Build timeline widget."""
        DirectLabel(
            text="Timeline",
            scale=0.05,
            pos=(-1.0, 0, 0.25),
            text_fg=self.accent_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        # Timeline widget
        self.timeline = TimelineWidget(
            parent=self.main_frame,
            x=-1.0,
            y=0.15,
            width=2.0,
            height=0.2,
            duration=1.0  # Will update when clip loads
        )
        
    def _build_parameter_panel(self):
        """Build parameter editing panel."""
        y_start = -0.15
        spacing = 0.12
        
        DirectLabel(
            text="Parameters",
            scale=0.05,
            pos=(-1.0, 0, y_start),
            text_fg=self.accent_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        # Duration slider
        self._add_param_label("Duration (s)", -1.0, y_start - spacing)
        self.duration_slider = self._add_slider(
            -0.5, y_start - spacing,
            min_val=0.1, max_val=5.0,
            initial=1.0,
            callback=self._on_duration_changed
        )
        
        # Looping checkbox
        self.looping_checkbox = DirectCheckButton(
            text="Looping",
            scale=0.045,
            pos=(-1.0, 0, y_start - spacing * 2),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            indicatorValue=1,
            boxBorder=0,
            boxRelief=DGG.FLAT,
            command=self._on_looping_changed,
            parent=self.main_frame
        )
        
    def _build_event_editor(self):
        """Build event timing editor."""
        y_start = -0.45
        spacing = 0.1
        
        DirectLabel(
            text="Events",
            scale=0.05,
            pos=(-1.0, 0, y_start),
            text_fg=self.accent_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        # Event list (simplified for now - just show count)
        self.event_count_label = DirectLabel(
            text="0 events",
            scale=0.04,
            pos=(-0.7, 0, y_start - spacing),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
        # Add event button
        DirectButton(
            text="+ Add Event",
            scale=0.045,
            pos=(-0.7, 0, y_start - spacing * 2),
            frameColor=self.accent_color,
            text_fg=(1, 1, 1, 1),
            command=self._on_add_event,
            parent=self.main_frame,
            relief=DGG.RAISED
        )
        
    def _build_footer(self):
        """Build footer with save/load buttons."""
        # Save button
        DirectButton(
            text="💾 Save to JSON",
            scale=0.05,
            pos=(-0.5, 0, -0.75),
            frameColor=self.btn_color,
            text_fg=(1, 1, 1, 1),
            command=self._on_save,
            parent=self.main_frame,
            relief=DGG.RAISED
        )
        
        # Reload button
        DirectButton(
            text="🔄 Reload",
            scale=0.05,
            pos=(0.0, 0, -0.75),
            frameColor=(0.5, 0.5, 0.5, 1),
            text_fg=(1, 1, 1, 1),
            command=self._on_reload,
            parent=self.main_frame,
            relief=DGG.RAISED
        )
        
        # Close hint
        DirectLabel(
            text="Press F4 to Close",
            scale=0.04,
            pos=(0, 0, -0.82),
            text_fg=(0.6, 0.6, 0.6, 1),
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
    def _add_param_label(self, text: str, x: float, y: float):
        """Helper to add parameter label."""
        DirectLabel(
            text=text,
            scale=0.04,
            pos=(x, 0, y),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        
    def _add_slider(self, x: float, y: float, min_val: float, max_val: float,
                    initial: float, callback):
        """Helper to add parameter slider."""
        slider = DirectSlider(
            range=(min_val, max_val),
            value=initial,
            pageSize=(max_val - min_val) / 10,
            scale=0.3,
            pos=(x, 0, y),
            command=callback,
            parent=self.main_frame
        )
        
        # Value label
        val_label = DirectLabel(
            text=f"{initial:.2f}",
            scale=0.04,
            pos=(x + 0.35, 0, y),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            frameColor=(0, 0, 0, 0),
            parent=self.main_frame
        )
        slider.val_label = val_label
        
        return slider
        
    # Event handlers
    
    def _on_clip_selected(self, clip_name: str):
        """Handle clip selection."""
        if clip_name == "(no clips)":
            return
            
        self.load_clip(clip_name)
        
    def _on_play(self):
        """Start playback."""
        if not self.current_clip:
            return
            
        self.playing = True
        if not self.update_task:
            self.update_task = self.base.taskMgr.add(self._update_playback, "AnimEditorUpdate")
            
    def _on_pause(self):
        """Pause playback."""
        self.playing = False
        
    def _on_stop(self):
        """Stop playback and reset to start."""
        self.playing = False
        self.current_time = 0.0
        self.timeline.set_playhead(0.0)
        self._update_time_display()
        
    def _step_frame(self, dt: float):
        """Step forward/backward by one frame."""
        if not self.current_clip:
            return
            
        self.current_time = max(0.0, min(self.current_time + dt, self.current_clip.duration))
        self.timeline.set_playhead(self.current_time)
        self._update_time_display()
        
    def _on_duration_changed(self):
        """Handle duration slider change."""
        if not self.current_clip:
            return
            
        new_duration = self.duration_slider['value']
        self.duration_slider.val_label['text'] = f"{new_duration:.2f}"
        
        # Update clip duration
        self.current_clip.duration = new_duration
        self.timeline.set_duration(new_duration)
        
    def _on_looping_changed(self, value):
        """Handle looping checkbox change."""
        if not self.current_clip:
            return
            
        self.current_clip.looping = bool(value)
        
    def _on_add_event(self):
        """Add a new event at current playhead time."""
        if not self.current_clip:
            return
            
        # Create new event at current time
        new_event = AnimationEvent(
            time=self.current_time,
            event_name="new_event",
            data={}
        )
        self.current_clip.events.append(new_event)
        
        # Refresh timeline
        self._refresh_timeline()
        
    def _on_save(self):
        """Save current clip to JSON."""
        if not self.current_clip or not self.current_clip_name:
            return
            
        # Save to data/animations directory
        output_dir = Path("data/animations")
        output_path = output_dir / f"{self.current_clip_name}.json"
        
        try:
            self.registry.save_to_json(self.current_clip_name, output_path)
            print(f"✅ Saved {self.current_clip_name} to {output_path}")
        except Exception as e:
            print(f"❌ Failed to save: {e}")
            
    def _on_reload(self):
        """Reload current clip from JSON."""
        if not self.current_clip_name:
            return
            
        json_path = Path(f"data/animations/{self.current_clip_name}.json")
        if json_path.exists():
            try:
                self.registry.reload_from_json(json_path)
                self.load_clip(self.current_clip_name)
                print(f"✅ Reloaded {self.current_clip_name}")
            except Exception as e:
                print(f"❌ Failed to reload: {e}")
        else:
            print(f"⚠️ No JSON file found for {self.current_clip_name}")
            
    # Core methods
    
    def load_clip(self, clip_name: str):
        """Load an animation clip into the editor.
        
        Args:
            clip_name: Name of clip to load
        """
        clip = self.registry.get_clip(clip_name)
        if not clip:
            return
            
        self.current_clip = clip
        self.current_clip_name = clip_name
        self.current_time = 0.0
        self.playing = False
        
        # Update UI
        self.duration_slider['value'] = clip.duration
        self.duration_slider.val_label['text'] = f"{clip.duration:.2f}"
        self.looping_checkbox['indicatorValue'] = 1 if clip.looping else 0
        
        # Update timeline
        self.timeline.set_duration(clip.duration)
        self._refresh_timeline()
        
        self._update_time_display()
        
    def _refresh_timeline(self):
        """Refresh timeline markers."""
        if not self.current_clip:
            return
            
        self.timeline.clear_markers()
        
        # Add keyframe markers
        for kf in self.current_clip.keyframes:
            self.timeline.add_keyframe_marker(kf.time)
            
        # Add event markers
        for event in self.current_clip.events:
            self.timeline.add_event_marker(event.time, event.event_name)
            
    def _update_playback(self, task):
        """Update task for playback."""
        if not self.playing or not self.current_clip:
            return task.cont
            
        dt = globalClock.getDt()
        self.current_time += dt
        
        # Handle looping
        if self.current_clip.looping:
            self.current_time = self.current_time % self.current_clip.duration
        else:
            if self.current_time >= self.current_clip.duration:
                self.current_time = self.current_clip.duration
                self.playing = False
                
        self.timeline.set_playhead(self.current_time)
        self._update_time_display()
        
        return task.cont
        
    def _update_time_display(self):
        """Update time label."""
        if self.current_clip:
            self.time_label['text'] = f"{self.current_time:.2f}s / {self.current_clip.duration:.2f}s"
        else:
            self.time_label['text'] = "0.00s / 0.00s"
