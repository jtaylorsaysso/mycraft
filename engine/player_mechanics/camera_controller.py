from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.rendering.camera import FPSCamera, ThirdPersonCamera
from engine.input.keybindings import InputAction

class CameraMechanic(PlayerMechanic):
    """Handles camera mode switching and updates."""
    
    priority = 10  # Run after movement, before animation
    exclusive = False
    
    def __init__(self, base):
        self.base = base
        self.camera_mode = 'third_person'
        self.fps_camera = None
        self.third_person_camera = None
        self.camera_controller = None
        self.toggle_cooldown = 0.0
    
    def initialize(self, player_id, world):
        """Called when player is ready (from coordinator)."""
        print(f"🔧 CameraMechanic.initialize() called")
        # Setup cameras
        self.fps_camera = FPSCamera(self.base.cam, None, sensitivity=40.0)
        self.third_person_camera = ThirdPersonCamera(self.base.cam, None, sensitivity=40.0)
        
        # Set active camera (default to third-person)
        self.camera_mode = 'third_person'
        self.camera_controller = self.third_person_camera
        
        self.base.cam.setHpr(0, 0, 0)
        print(f"📷 Camera initialized in {self.camera_mode} mode")
        print(f"   - FPS camera: {self.fps_camera}")
        print(f"   - Third-person camera: {self.third_person_camera}")
        print(f"   - Active controller: {self.camera_controller}")
    
    def update(self, ctx: PlayerContext) -> None:
        # Write mode to context FIRST so other mechanics see correct mode
        ctx.camera_mode = self.camera_mode
        
        # Handle toggle
        self.toggle_cooldown = max(0, self.toggle_cooldown - ctx.dt)
        
        # Debug Camera Toggle detection via Action
        if ctx.input.is_action_active(InputAction.CAMERA_TOGGLE_MODE):
            print(f"🔍 Camera Toggle action active! cooldown={self.toggle_cooldown:.2f}, mode={self.camera_mode}")
        
        if ctx.input.is_action_active(InputAction.CAMERA_TOGGLE_MODE) and self.toggle_cooldown <= 0:
            print(f"🔄 Toggling camera mode from {self.camera_mode}")
            self._toggle_camera_mode()
            self.toggle_cooldown = 0.3
            # Update context with new mode immediately
            ctx.camera_mode = self.camera_mode
            print(f"   → New mode: {self.camera_mode}, controller: {self.camera_controller}")
        
        # Update settings from config if available
        if hasattr(self.base, 'config_manager') and self.base.config_manager:
            sensitivity = self.base.config_manager.get("mouse_sensitivity", 40.0)
            fov = self.base.config_manager.get("fov", 90.0)
            
            # Apply FOV
            self.base.camLens.setFov(fov)
            
            # Apply sensitivity (update controllers)
            self.fps_camera.sensitivity = sensitivity
            self.third_person_camera.sensitivity = sensitivity
            
            # Apply camera distance (third-person only)
            cam_dist = self.base.config_manager.get("camera_distance", 4.0)
            self.third_person_camera.set_distance(cam_dist)

        # Update active camera
        if self.camera_mode == 'third_person':
            self.camera_controller.update(
                ctx.input.mouse_delta[0],
                ctx.input.mouse_delta[1],
                ctx.dt,
                ctx.transform.position
            )
        else:
            # First-person mode
            # Update camera rotation first
            self.camera_controller.update(
                ctx.input.mouse_delta[0],
                ctx.input.mouse_delta[1],
                ctx.dt
            )
            # Then set position at player eye level
            from panda3d.core import LVector3f
            cam_offset = LVector3f(0, 0, 1.8)
            self.base.cam.setPos(ctx.transform.position + cam_offset)
    
    def _toggle_camera_mode(self):
        if self.camera_mode == 'third_person':
            self.camera_mode = 'first_person'
            self.camera_controller = self.fps_camera
            print("📷 Switched to First-Person")
        else:
            self.camera_mode = 'third_person'
            self.camera_controller = self.third_person_camera
            print("📷 Switched to Third-Person")
