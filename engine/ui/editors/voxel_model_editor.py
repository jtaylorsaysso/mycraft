"""
Voxel Model Editor for creating characters and assets.
"""
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DGG
from panda3d.core import NodePath, WindowProperties, Vec3, Point3
import math

from engine.ui.base_editor import BaseEditorWindow
from engine.ui.editors.voxel_canvas import VoxelCanvas

class VoxelModelEditorWindow(BaseEditorWindow):
    """
    Editor for creating 3D voxel models and skins.
    """
    
    def __init__(self, base):
        # Attribute initialization BEFORE super().__init__ which calls setup/hide
        self.canvas = None
        self.cam_pivot = None
        self.saved_cam_parent = None
        self.saved_cam_transform = None
        
        # Camera State
        self.orbit_distance = 10.0
        self.orbit_pitch = -30.0
        self.orbit_heading = 0.0
        self.is_orbiting = False
        
        # Tools
        self.selected_tool = "Pencil"
        self.selected_color = (1, 1, 1, 1)
        
        self.update_task = None
        
        super().__init__(base, "Model Editor")
        
    def setup(self):
        """Initialize Model Editor UI and Canvas."""
        # 1. Canvas
        self.canvas = VoxelCanvas(self.base)
        # Move canvas to a safe spot or use a display region?
        # For now, we will just interact with its root node.
        self.canvas.root.reparentTo(self.base.render)
        self.canvas.root.hide() # Hidden by default
        
        # 2. UI Layout
        self._build_sidebar_left()
        self._build_sidebar_right()
        self._build_toolbar()
        
        self.canvas.add_voxel((0,0,0), (1,0,0,1)) # Test Voxel
        
    def show(self):
        """Enable editor mode."""
        super().show()
        
        # 1. Show Canvas
        self.canvas.root.show()
        
        # 2. Takeover Camera
        self.saved_cam_parent = self.base.camera.getParent()
        self.saved_cam_transform = self.base.camera.getTransform()
        
        # Create Pivot
        self.cam_pivot = self.base.render.attachNewNode("EditorCamPivot")
        self.cam_pivot.setPos(0, 0, 0)
        
        self.base.camera.reparentTo(self.cam_pivot)
        self.base.camera.setPos(0, -self.orbit_distance, 0)
        self.base.camera.lookAt(0, 0, 0)
        
        self._update_camera()
        
        # 3. Input Overrides
        # We need mouse input for camera and tools
        self.accept("mouse3", self._start_orbit)
        self.accept("mouse3-up", self._stop_orbit)
        self.accept("wheel_up", self._zoom_in)
        self.accept("wheel_down", self._zoom_out)
        
        # Task for orbitting
        self.update_task = self.base.taskMgr.add(self._update_editor, "ModelEditorUpdate")
        
        # Hide Game World (Optional, if we want clean void)
        # self.base.game_world_root.hide() # If available
        
    def hide(self):
        """Disable editor mode."""
        super().hide()
        
        # 1. Hide Canvas
        if self.canvas:
            self.canvas.root.hide()
            
        # 2. Restore Camera
        if self.saved_cam_parent:
            self.base.camera.reparentTo(self.saved_cam_parent)
            self.base.camera.setTransform(self.saved_cam_transform)
            
        if self.cam_pivot:
            self.cam_pivot.removeNode()
            self.cam_pivot = None
            
        # 3. Cleanup Inputs
        self.ignore("mouse3")
        self.ignore("mouse3-up")
        self.ignore("wheel_up")
        self.ignore("wheel_down")
        
        if self.update_task:
            self.base.taskMgr.remove(self.update_task)
            self.update_task = None
            
    def _update_editor(self, task):
        """Frame update for camera and interaction."""
        if self.is_orbiting:
            md = self.base.win.getPointer(0)
            x = md.getX()
            y = md.getY()
            
            if hasattr(self, 'last_mouse_x'):
                dx = x - self.last_mouse_x
                dy = y - self.last_mouse_y
                
                self.orbit_heading -= dx * 0.5
                self.orbit_pitch = min(max(self.orbit_pitch - dy * 0.5, -89), 89)
                self._update_camera()
                
            self.last_mouse_x = x
            self.last_mouse_y = y
            
        return task.cont
        
    def _start_orbit(self):
        self.is_orbiting = True
        md = self.base.win.getPointer(0)
        self.last_mouse_x = md.getX()
        self.last_mouse_y = md.getY()
        
    def _stop_orbit(self):
        self.is_orbiting = False
        
    def _zoom_in(self):
        self.orbit_distance = max(1.0, self.orbit_distance - 1.0)
        self._update_camera()
        
    def _zoom_out(self):
        self.orbit_distance = min(50.0, self.orbit_distance + 1.0)
        self._update_camera()

    def _update_camera(self):
        if not self.cam_pivot:
            return
        self.cam_pivot.setHpr(self.orbit_heading, self.orbit_pitch, 0)
        self.base.camera.setPos(0, -self.orbit_distance, 0)

    # UI Construction
    
    def _build_sidebar_left(self):
        """Tools and Palette."""
        frame = self._create_panel((-1.2, -0.9, -0.9, 0.9), "Tools")
        
        # Tool Buttons
        y = 0.7
        for tool in ["Pencil", "Eraser", "Picker"]:
            DirectButton(
                parent=frame,
                text=tool,
                scale=0.05,
                pos=(0.15, 0, y),
                frameColor=(0.2, 0.2, 0.2, 1),
                text_fg=(1,1,1,1),
                command=self._select_tool,
                extraArgs=[tool]
            )
            y -= 0.15
            
        # Color Palette Stub
        DirectLabel(parent=frame, text="Palette", scale=0.05, pos=(0.15, 0, 0.2), text_fg=(1,1,1,1), frameColor=(0,0,0,0))
        # TODO: Grid of colors
            
    def _build_sidebar_right(self):
        """Layers and Properties."""
        frame = self._create_panel((0.9, 1.2, -0.9, 0.9), "Layers")
        DirectButton(parent=frame, text="+ Layer", scale=0.05, pos=(0.15, 0, 0.7))
        
    def _build_toolbar(self):
        """Top bar."""
        frame = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-1.3, 1.3, 0.85, 0.95),
            pos=(0, 0, 0)
        )
        DirectLabel(parent=frame, text="Model Editor", scale=0.04, pos=(-1.1, 0, 0.88), text_fg=(1,1,1,1), frameColor=(0,0,0,0))

    def _create_panel(self, frame_size, title):
        """Helper to create standard side panel."""
        frame = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.12, 0.12, 0.12, 0.95),
            frameSize=frame_size,
            pos=(0, 0, 0),
            relief=DGG.FLAT
        )
        # Title
        DirectLabel(
            parent=frame,
            text=title,
            scale=0.05,
            pos=(frame_size[0] + 0.15, 0, frame_size[3] - 0.05),
            text_fg=(0.8, 0.8, 0.8, 1),
            frameColor=(0,0,0,0)
        )
        return frame
        
    def _select_tool(self, tool_name):
        self.selected_tool = tool_name
        print(f"Tool selected: {tool_name}")

    def cleanup(self):
        """Clean up resources."""
        self.hide()
        if self.canvas:
            self.canvas.cleanup()
        super().cleanup()
