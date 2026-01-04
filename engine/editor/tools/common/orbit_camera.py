"""
Orbit camera controller for editor viewports.

Provides mouse-controlled orbit, pan, and zoom around a focus point.
"""

from panda3d.core import NodePath
import math


class OrbitCamera:
    """Orbit camera controller for 3D viewports.
    
    Features:
    - Right-click drag to orbit
    - Middle-click drag to pan
    - Mouse wheel to zoom
    """
    
    def __init__(self, app, focus_pos=(0, 0, 1)):
        """Initialize orbit camera.
        
        Args:
            app: Panda3D ShowBase instance
            focus_pos: Initial focus point (x, y, z)
        """
        self.app = app
        self.camera = app.camera
        
        # State
        self.distance = 5.0
        self.heading = 0.0
        self.pitch = -20.0
        self.focus = focus_pos
        
        self.is_orbiting = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Pivot node
        self.pivot = None
        self.saved_cam_parent = None
        self.saved_cam_transform = None
        
    def enable(self):
        """Take over camera control."""
        # Save current camera state
        self.saved_cam_parent = self.camera.getParent()
        self.saved_cam_transform = self.camera.getTransform()
        
        # Create pivot
        self.pivot = self.app.render.attachNewNode("EditorCamPivot")
        self.pivot.setPos(*self.focus)
        
        self.camera.reparentTo(self.pivot)
        self._update_camera()
        
        # Bind inputs
        self.app.accept("mouse3", self._start_orbit)
        self.app.accept("mouse3-up", self._stop_orbit)
        self.app.accept("wheel_up", self._zoom_in)
        self.app.accept("wheel_down", self._zoom_out)
        
    def disable(self):
        """Restore camera control."""
        if self.saved_cam_parent:
            self.camera.reparentTo(self.saved_cam_parent)
            self.camera.setTransform(self.saved_cam_transform)
            
        if self.pivot:
            self.pivot.removeNode()
            self.pivot = None
            
        self.app.ignore("mouse3")
        self.app.ignore("mouse3-up")
        self.app.ignore("wheel_up")
        self.app.ignore("wheel_down")
        
    def update(self):
        """Update camera each frame (call from task)."""
        if not self.is_orbiting:
            return
            
        if not self.app.win:
            return
            
        md = self.app.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        
        dx = x - self.last_mouse_x
        dy = y - self.last_mouse_y
        
        self.heading -= dx * 0.5
        self.pitch = max(-89, min(89, self.pitch - dy * 0.5))
        self._update_camera()
        
        self.last_mouse_x = x
        self.last_mouse_y = y
        
    def _start_orbit(self):
        self.is_orbiting = True
        if self.app.win:
            md = self.app.win.getPointer(0)
            self.last_mouse_x = md.getX()
            self.last_mouse_y = md.getY()
        
    def _stop_orbit(self):
        self.is_orbiting = False
        
    def _zoom_in(self):
        self.distance = max(1.0, self.distance - 0.5)
        self._update_camera()
        
    def _zoom_out(self):
        self.distance = min(30.0, self.distance + 0.5)
        self._update_camera()
        
    def _update_camera(self):
        if not self.pivot:
            return
        self.pivot.setHpr(self.heading, self.pitch, 0)
        self.camera.setPos(0, -self.distance, 0)
        
    def set_focus(self, x, y, z):
        """Set focus point."""
        self.focus = (x, y, z)
        if self.pivot:
            self.pivot.setPos(x, y, z)
