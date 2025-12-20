"""Player control system using native Panda3D InputManager."""

from engine.ecs.system import System
from engine.input.manager import InputManager, KeyBindings
from engine.rendering.camera import FPSCamera
from engine.components.core import Transform
from panda3d.core import LVector3f
import math

class PlayerControlSystem(System):
    """System that handles player movement and camera controls."""
    
    def __init__(self, world, event_bus, base):
        super().__init__(world, event_bus)
        self.base = base
        self.input = InputManager()
        self.camera_controller = None
        
    def initialize(self):
        """Setup camera when system is added."""
        # Find player entity
        player_id = self.world.get_entity_by_tag("player")
        if player_id:
            # Setup FPS camera
            self.camera_controller = FPSCamera(self.base.cam, sensitivity=40.0)
            
            # Set initial camera orientation (look down slightly to see water)
            self.base.cam.setHpr(0, -20, 0)  # Heading=0, Pitch=-20 (look down), Roll=0
            
            self.input.lock_mouse()

    def update(self, dt):
        """Process input and update player transform."""
        self.input.update()
        
        player_id = self.world.get_entity_by_tag("player")
        if not player_id or not self.camera_controller:
            return
        transform = self.world.get_component(player_id, Transform)
        if not transform:
            return

        # Update camera (rotation)
        self.camera_controller.update(dt, self.input)
        
        # Movement
        move_vec = LVector3f(0, 0, 0)
        
        # Get forward/right vectors from camera HPR
        h = self.base.cam.getH()
        rad = math.radians(h)
        forward = LVector3f(-math.sin(rad), math.cos(rad), 0)
        right = LVector3f(math.cos(rad), math.sin(rad), 0)
        
        if self.input.is_key_down('w'): move_vec += forward
        if self.input.is_key_down('s'): move_vec -= forward
        if self.input.is_key_down('a'): move_vec -= right
        if self.input.is_key_down('d'): move_vec += right
        
        if move_vec.length() > 0:
            move_vec.normalize()
            speed = 6.0
            transform.position += move_vec * speed * dt
            
        # Update camera position to follow player (head height)
        # Panda3D uses Y-forward, Z-up coordinate system
        cam_offset = LVector3f(0, 0, 1.8)  # 1.8 units above player position
        self.base.cam.setPos(transform.position + cam_offset)
        
        # Debug toggle
        if self.input.is_key_down('escape'):
            self.input.unlock_mouse()
