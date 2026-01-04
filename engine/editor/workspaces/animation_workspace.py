
from typing import Optional
from direct.gui.DirectGui import DirectEntry, DirectFrame, DirectLabel, DirectButton, DGG
from panda3d.core import NodePath, ClockObject

from engine.editor.workspace import Workspace
from engine.editor.panels.clip_browser_panel import ClipBrowserPanel
from engine.editor.panels.timeline_panel import TimelinePanel

from engine.animation.skeleton import HumanoidSkeleton
from engine.animation.voxel_avatar import VoxelAvatar
from engine.animation.core import AnimationClip, Keyframe, Transform
from engine.core.logger import get_logger

logger = get_logger(__name__)

class AnimationWorkspace(Workspace):
    """Animation editing workspace."""
    
    def __init__(self, app):
        super().__init__(app, "Animation")
        
        self.registry = app.anim_registry
        
        # Playback State
        self.current_clip: Optional[AnimationClip] = None
        self.current_clip_name: Optional[str] = None
        self.playing = False
        self.current_time = 0.0
        
        # 3D Content
        self.preview_root: Optional[NodePath] = None
        self.preview_avatar = None
        self.preview_skeleton = None
        
        # Panels
        self.browser_panel: Optional[ClipBrowserPanel] = None
        self.timeline_panel: Optional[TimelinePanel] = None
        self.io_dialog_frame = None
        
        self.update_task = None
        
        self._setup_scene()
        self._build_ui()
        
    def _setup_scene(self):
        """Initialize 3D preview."""
        self.preview_root = self.app.render.attachNewNode("AnimPreview")
        self.preview_root.hide() # Hidden until active
        
        # Create preview avatar
        self.preview_skeleton = HumanoidSkeleton()
        self.preview_avatar = VoxelAvatar(
            self.preview_root,
            skeleton=self.preview_skeleton,
            body_color=(0.3, 0.7, 1.0, 1.0)
        )
        
    def _build_ui(self):
        """Build workspace UI."""
        # Browser Panel
        callbacks_browser = {
            'on_clip_select': self._on_clip_selected,
            'on_new': self._on_new_clip,
            'on_save': self._on_save,
            'on_load': self._on_load
        }
        self.browser_panel = ClipBrowserPanel(self.app.aspect2d, self.registry, callbacks_browser)
        self.browser_panel.frame.hide()
        
        # Timeline Panel
        callbacks_timeline = {
            'play': self._on_play,
            'pause': self._on_pause,
            'stop': self._on_stop,
            'capture': self._on_capture_keyframe,
            'delete_key': self._delete_selected_keyframe,
            'looping': self._on_looping_changed
        }
        self.timeline_panel = TimelinePanel(self.app.aspect2d, callbacks_timeline)
        self.timeline_panel.frame.hide()

    # ─────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────

    def enter(self):
        super().enter()
        self.preview_root.show()
        self.browser_panel.frame.show()
        self.timeline_panel.frame.show()
        
        # Setup camera
        # WorkspaceManager doesn't enforce cam, so we set it here
        # Assuming OrbitCamera interaction isn't needed here yet, just static view
        self.app.camera.setPos(5, 5, 2)
        self.app.camera.lookAt(self.preview_root)
        
        self._refresh_clip_list()
        
    def exit(self):
        super().exit()
        self.preview_root.hide()
        self.browser_panel.frame.hide()
        self.timeline_panel.frame.hide()
        self._stop_playback()
        
    def accept_shortcuts(self):
        self.app.accept('space', self._toggle_playback)
        self.app.accept('x', self._delete_selected_keyframe)

    # ─────────────────────────────────────────────────────────────────
    # Logic
    # ─────────────────────────────────────────────────────────────────
    
    def _toggle_playback(self):
        if self.playing: self._on_pause()
        else: self._on_play()

    def _on_play(self):
        if not self.current_clip: return
        self.playing = True
        if not self.update_task:
            self.update_task = self.app.taskMgr.add(self._update_playback, "AnimWSUpdate")
            
    def _on_pause(self):
        self.playing = False
        
    def _on_stop(self):
        self._stop_playback()
        self.current_time = 0.0
        self._update_timeline_ui()
        
    def _stop_playback(self):
        self.playing = False
        if self.update_task:
            self.app.taskMgr.remove(self.update_task)
            self.update_task = None
            
    def _update_playback(self, task):
        if not self.playing or not self.current_clip:
            return task.cont
        
        dt = ClockObject.getGlobalClock().getDt()
        self.current_time += dt
        
        if self.current_clip.looping:
            self.current_time %= self.current_clip.duration
        elif self.current_time >= self.current_clip.duration:
            self.current_time = self.current_clip.duration
            self.playing = False
            
        self._update_timeline_ui()
        self._apply_pose()
        return task.cont
        
    def _update_timeline_ui(self):
        dur = self.current_clip.duration if self.current_clip else 1.0
        self.timeline_panel.update_time(self.current_time, dur)
        
    def _apply_pose(self):
        if self.preview_skeleton and self.current_clip:
            pose = self.current_clip.get_pose(self.current_time)
            self.preview_skeleton.apply_pose(pose)

    def _on_clip_selected(self, clip_name):
        if clip_name == "(no clips)": return
        clip = self.registry.get_clip(clip_name)
        if not clip: return
        
        self.current_clip = clip
        self.current_clip_name = clip_name
        self._stop_playback()
        
        # Update UI
        self.browser_panel.set_selected(clip_name)
        self.timeline_panel.set_duration(clip.duration)
        self.timeline_panel.set_looping(clip.looping)
        
        # Markers
        self.timeline_panel.timeline.clear_markers()
        for kf in clip.keyframes:
            self.timeline_panel.timeline.add_keyframe_marker(kf.time)
            
        self._update_timeline_ui()
        self._apply_pose()
        
    def _refresh_clip_list(self):
        self.browser_panel.refresh_clip_list()
        # Auto select first
        items = self.browser_panel.clip_dropdown['items']
        if items and items[0] != "(no clips)":
            if not self.current_clip_name or self.current_clip_name not in items:
                self._on_clip_selected(items[0])
            else:
                self.browser_panel.set_selected(self.current_clip_name)
                
    def _on_new_clip(self):
        clip = AnimationClip(name="new_clip", duration=1.0, looping=True, keyframes=[])
        self.registry.register_clip(clip)
        self._refresh_clip_list()
        self._on_clip_selected("new_clip")
        
    def _on_capture_keyframe(self):
        if not self.current_clip or not self.preview_skeleton: return
        
        # For now, just capture current pose (which is silly if we just playing it back)
        # Real usage: This workspace would need a Bone Drag mode to pose the character.
        # But for now we just verify structural porting.
        # Let's assume user posed it via some other tool? Or maybe enable dragging here too?
        # For simplicity (Phase 3 scope), just capture whatever pose is currently applied.
        
        transforms = {}
        for bone_name, bone in self.preview_skeleton.bones.items():
            transforms[bone_name] = Transform(
                position=bone.node.getPos(),
                rotation=bone.node.getHpr(),
                scale=bone.node.getScale()
            )
            
        new_kf = Keyframe(time=self.current_time, transforms=transforms)
        self.current_clip.keyframes.append(new_kf)
        self.current_clip.keyframes.sort(key=lambda k: k.time)
        
        self.timeline_panel.timeline.add_keyframe_marker(self.current_time)
        logger.info(f"Captured keyframe at {self.current_time:.2f}s")
        
    def _delete_selected_keyframe(self):
        if not self.current_clip: return
        time = self.current_time
        tolerance = 0.05
        
        target = None
        for kf in self.current_clip.keyframes:
            if abs(kf.time - time) < tolerance:
                target = kf
                break
        
        if target:
            self.current_clip.keyframes.remove(target)
            self._on_clip_selected(self.current_clip_name) # Refresh UI
            logger.info("Deleted keyframe")
            
    def _on_looping_changed(self, value):
        if self.current_clip:
            self.current_clip.looping = bool(value)

    # ─────────────────────────────────────────────────────────────────
    # I/O Dialog (Simplified Modal)
    # ─────────────────────────────────────────────────────────────────
    
    def _on_save(self):
        if self.current_clip: self._show_io_dialog("Save As:", self._execute_save)
        
    def _on_load(self):
        self._show_io_dialog("Load Clip:", self._execute_load)

    def _show_io_dialog(self, title, callback):
        if self.io_dialog_frame: self.io_dialog_frame.destroy()
        
        # Fullscreen Blocker
        self.io_dialog_frame = DirectFrame(parent=self.app.aspect2d, frameColor=(0,0,0,0.8), frameSize=(-2,2,-2,2), pos=(0,0,0))
        
        panel = DirectFrame(parent=self.io_dialog_frame, frameColor=(0.2,0.2,0.2,1), frameSize=(-0.5,0.5,-0.2,0.2))
        DirectLabel(parent=panel, text=title, scale=0.05, pos=(0,0,0.1), text_fg=(1,1,1,1))
        entry = DirectEntry(parent=panel, scale=0.05, pos=(-0.3,0,-0.05), width=12, initialText="", focus=1)
        
        def commit():
            txt = entry.get()
            self.io_dialog_frame.destroy()
            self.io_dialog_frame = None
            callback(txt)
            
        def cancel():
            self.io_dialog_frame.destroy()
            self.io_dialog_frame = None
            
        DirectButton(parent=panel, text="OK", scale=0.05, pos=(0.2,0,-0.15), command=commit)
        DirectButton(parent=panel, text="Cancel", scale=0.05, pos=(-0.2,0,-0.15), command=cancel)
        
    def _execute_save(self, name):
        if not name or not self.current_clip: return
        self.current_clip.name = name
        self.app.asset_manager.save_animation_clip(self.current_clip, name)
        self.registry.register_clip(self.current_clip)
        self._refresh_clip_list()
        
    def _execute_load(self, name):
        if not name:
            logger.warning("Load cancelled: no name provided")
            return
            
        try:
            clip = self.app.asset_manager.load_animation_clip(name)
            self.registry.register_clip(clip)
            self._refresh_clip_list()
            self._on_clip_selected(clip.name)
            logger.info(f"Loaded clip: {clip.name}")
        except FileNotFoundError:
            logger.error(f"Clip file not found: {name}")
        except Exception as e:
            logger.error(f"Failed to load clip '{name}': {e}")

    def cleanup(self):
        super().cleanup()
        if self.preview_root: self.preview_root.removeNode()
        if self.browser_panel: self.browser_panel.cleanup()
        if self.timeline_panel: self.timeline_panel.cleanup()
