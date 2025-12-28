from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.rendering.camera import FPSCamera, ThirdPersonCamera
from engine.input.keybindings import InputAction
from engine.components.camera_state import CameraState, CameraMode

class CameraMechanic(PlayerMechanic):
    """Handles camera mode switching and updates."""
    
    priority = 10  # Run after movement, before animation
    exclusive = False
    
    def __init__(self, base):
        self.base = base
        self.fps_camera = None
        self.third_person_camera = None
        self.camera_controller = None
    
    def initialize(self, player_id, world):
        """Called when player is ready (from coordinator)."""
        print(f"🔧 CameraMechanic.initialize() called")
        
        # Get collision system from world (set by PlayerControlSystem)
        collision_traverser = getattr(world, 'collision_traverser', None)
        render_node = self.base.render
        
        # Get camera configuration
        side_offset = 1.0  # Default
        if hasattr(self.base, 'config_manager') and self.base.config_manager:
            side_offset = self.base.config_manager.get("camera_side_offset", 1.0)
        
        # Setup cameras
        self.fps_camera = FPSCamera(self.base.cam, None, sensitivity=40.0)
        self.third_person_camera = ThirdPersonCamera(
            self.base.cam, None, sensitivity=40.0,
            collision_traverser=collision_traverser,
            render_node=render_node,
            side_offset=side_offset
        )
        
        # Set active camera (default to third-person)
        self.camera_controller = self.third_person_camera
        
        # Initialize CameraState component if not exists
        from engine.components.core import CameraState, CameraMode
        camera_state = world.get_component(player_id, CameraState)
        if not camera_state:
            camera_state = CameraState(
                mode=CameraMode.THIRD_PERSON,
                yaw=0.0,
                pitch=-15.0,  # Looking down slightly
                distance=5.0,
                current_distance=5.0
            )
            world.add_component(player_id, camera_state)
        
        self.base.cam.setHpr(0, 0, 0)
        print(f"📷 Camera initialized in {camera_state.mode.name} mode")
        print(f"   - FPS camera: {self.fps_camera}")
        print(f"   - Third-person camera: {self.third_person_camera}")
        print(f"   - Active controller: {self.camera_controller}")
        print(f"   - Collision detection: {'enabled' if collision_traverser else 'disabled'}")
        print(f"   - Side offset: {side_offset}")
    
    def update(self, ctx: PlayerContext) -> None:
        # Get camera state from ECS
        camera_state = ctx.world.get_component(ctx.player_id, CameraState)
        if not camera_state:
            return
        
        # Handle toggle cooldown
        camera_state.toggle_cooldown = max(0, camera_state.toggle_cooldown - ctx.dt)
        
        # Debug Camera Toggle detection via Action
        if ctx.input.is_action_active(InputAction.CAMERA_TOGGLE_MODE):
            print(f"🔍 Camera Toggle action active! cooldown={camera_state.toggle_cooldown:.2f}, mode={camera_state.mode.name}")
        
        if ctx.input.is_action_active(InputAction.CAMERA_TOGGLE_MODE) and camera_state.toggle_cooldown <= 0:
            print(f"🔄 Toggling camera mode from {camera_state.mode.name}")
            self._toggle_camera_mode(camera_state)
            camera_state.toggle_cooldown = 0.3
            print(f"   → New mode: {camera_state.mode.name}, controller: {self.camera_controller}")
        
        # Handle scroll wheel zoom (third-person only)
        if camera_state.mode == CameraMode.THIRD_PERSON:
            scroll = ctx.input.scroll_delta
            if scroll != 0:
                zoom_speed = 0.5  # Distance change per scroll notch
                new_distance = camera_state.distance - (scroll * zoom_speed)
                self.third_person_camera.set_distance(camera_state, new_distance)
        
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
            self.third_person_camera.set_distance(camera_state, cam_dist)
            
            # Apply camera side offset (third-person only)
            side_offset = self.base.config_manager.get("camera_side_offset", 1.0)
            self.third_person_camera.side_offset = side_offset

        # Update active camera
        if camera_state.mode == CameraMode.THIRD_PERSON:
            # Get player velocity for camera bob
            from panda3d.core import LVector3f
            player_velocity = LVector3f(ctx.state.velocity_x, ctx.state.velocity_y, ctx.state.velocity_z)
            
            self.camera_controller.update(
                ctx.input.mouse_delta[0],
                ctx.input.mouse_delta[1],
                ctx.dt,
                ctx.transform.position,
                camera_state,
                player_velocity
            )
        else:
            # First-person mode
            # Update camera rotation first
            self.camera_controller.update(
                ctx.input.mouse_delta[0],
                ctx.input.mouse_delta[1],
                camera_state,
                ctx.dt
            )
            # Then set position at player eye level
            from panda3d.core import LVector3f
            cam_offset = LVector3f(0, 0, 1.8)
            self.base.cam.setPos(ctx.transform.position + cam_offset)
    
    def _toggle_camera_mode(self, camera_state: CameraState):
        if camera_state.mode == CameraMode.THIRD_PERSON:
            camera_state.mode = CameraMode.FIRST_PERSON
            self.camera_controller = self.fps_camera
            print("📷 Switched to First-Person")
        else:
            camera_state.mode = CameraMode.THIRD_PERSON
            self.camera_controller = self.third_person_camera
            print("📷 Switched to Third-Person")
