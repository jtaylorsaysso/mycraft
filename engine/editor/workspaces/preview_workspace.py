
from typing import Optional
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from panda3d.core import NodePath, TextNode, ClockObject

from engine.editor.workspace import Workspace
from engine.animation.skeleton import HumanoidSkeleton
from engine.animation.voxel_avatar import VoxelAvatar
from engine.core.logger import get_logger

logger = get_logger(__name__)

class PreviewWorkspace(Workspace):
    """Preview workspace for full-screen playback."""
    
    def __init__(self, app):
        super().__init__(app, "Preview")
        
        # 3D Content
        self.preview_root: Optional[NodePath] = None
        self.avatar = None
        self.skeleton = None
        
        # UI
        self.controls_frame = None
        self.play_btn = None
        
        # State
        self.playing = False
        self.current_time = 0.0
        self.current_clip = None
        
        self.update_task = None
        
        self._setup_scene()
        self._build_ui()
        
    def _setup_scene(self):
        self.preview_root = self.app.render.attachNewNode("PreviewRoot")
        self.preview_root.hide() 
        
        self.skeleton = HumanoidSkeleton()
        self.avatar = VoxelAvatar(
            self.preview_root,
            skeleton=self.skeleton,
            body_color=(0.3, 0.7, 1.0, 1.0)
        )
        
    def _build_ui(self):
        """Floating playback controls at bottom center."""
        self.controls_frame = DirectFrame(
            parent=self.app.aspect2d,
            frameColor=(0, 0, 0, 0.5), # Transparent black
            frameSize=(-0.4, 0.4, -0.1, 0.1),
            pos=(0, 0, -0.85)
        )
        self.controls_frame.hide()
        
        self.play_btn = DirectButton(
            parent=self.controls_frame,
            text="> Play",
            scale=0.05,
            pos=(-0.2, 0, -0.015),
            frameColor=(0.2, 0.6, 0.2, 1),
            text_fg=(1, 1, 1, 1),
            command=self._toggle_playback
        )
        
        DirectButton(
            parent=self.controls_frame,
            text="Reset",
            scale=0.05,
            pos=(0.2, 0, -0.015),
            frameColor=(0.4, 0.4, 0.45, 1),
            text_fg=(1, 1, 1, 1),
            command=self._reset_playback
        )
        
        self.info_label = DirectLabel(
            parent=self.controls_frame,
            text="No Clip",
            scale=0.04,
            pos=(0, 0, 0.06),
            text_fg=(0.8, 0.8, 0.8, 1),
            frameColor=(0,0,0,0)
        )

    def enter(self):
        super().enter()
        self.preview_root.show()
        self.controls_frame.show()
        
        # Position camera for nice view
        self.app.camera.setPos(6, 6, 2.5)
        self.app.camera.lookAt(self.preview_root)
        
        # Try to load a clip if one was active in Animation Workspace?
        # For now, just reset
        self._reset_playback()
        
    def exit(self):
        super().exit()
        self.preview_root.hide()
        self.controls_frame.hide()
        self._stop_playback()
        
    def accept_shortcuts(self):
        self.app.accept('space', self._toggle_playback)

    def _toggle_playback(self):
        if self.playing:
            self._stop_playback()
            self.play_btn['text'] = "> Play"
        else:
            self._start_playback()
            self.play_btn['text'] = "|| Pause"
            
    def _start_playback(self):
        # Find a clip from registry if none
        if not self.current_clip:
             clips = self.app.anim_registry.list_clips()
             if clips:
                 self.current_clip = self.app.anim_registry.get_clip(clips[0])
                 self.info_label['text'] = f"Playing: {self.current_clip.name}"
             else:
                 self.info_label['text'] = "No clips found"
                 return
                 
        self.playing = True
        if not self.update_task:
            self.update_task = self.app.taskMgr.add(self._update, "PreviewUpdate")
            
    def _stop_playback(self):
        self.playing = False
        if self.update_task:
            self.app.taskMgr.remove(self.update_task)
            self.update_task = None
            
    def _reset_playback(self):
        self._stop_playback()
        self.current_time = 0.0
        if self.play_btn: self.play_btn['text'] = "> Play"
        
        # Reset pose
        if self.skeleton:
            self.skeleton.reset_pose()
            
    def _update(self, task):
        if not self.playing or not self.current_clip:
            return task.cont
            
        dt = ClockObject.getGlobalClock().getDt()
        self.current_time += dt
        
        if self.current_clip.looping:
            self.current_time %= self.current_clip.duration
        elif self.current_time >= self.current_clip.duration:
            self.current_time = self.current_clip.duration
            self.playing = False
            self.play_btn['text'] = "> Play"
            
        # Apply Pose with error handling
        try:
            pose = self.current_clip.get_pose(self.current_time)
            self.skeleton.apply_pose(pose)
        except Exception as e:
            logger.error(f"Failed to apply pose at time {self.current_time}: {e}")
            self._stop_playback()
            
        return task.cont
        
    def cleanup(self):
        super().cleanup()
        if self.preview_root: self.preview_root.removeNode()
        if self.controls_frame: self.controls_frame.destroy()
