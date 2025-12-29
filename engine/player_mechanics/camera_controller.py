from typing import Dict, Optional
from panda3d.core import LVector3f
from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.rendering.base_camera import BaseCamera, CameraUpdateContext
from engine.rendering.first_person_camera import FirstPersonCamera
from engine.rendering.exploration_camera import ExplorationCamera
from engine.rendering.combat_camera import CombatCamera
from engine.input.keybindings import InputAction
from engine.components.camera_state import CameraState, CameraMode


class CameraMechanic(PlayerMechanic):
    """Handles camera mode switching and updates.
    
    Uses a registry of camera mode implementations that can be
    switched based on game/player state.
    """
    
    priority = 10  # Run after movement, before animation
    exclusive = False
    
    def __init__(self, base):
        self.base = base
        self.cameras: Dict[CameraMode, BaseCamera] = {}
        self.active_camera: Optional[BaseCamera] = None
    
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
        
        # Create all camera modes
        self.cameras = {
            CameraMode.FIRST_PERSON: FirstPersonCamera(
                self.base.cam, 
                sensitivity=40.0
            ),
            CameraMode.EXPLORATION: ExplorationCamera(
                self.base.cam,
                sensitivity=40.0,
                collision_traverser=collision_traverser,
                render_node=render_node,
                side_offset=side_offset
            ),
            CameraMode.COMBAT: CombatCamera(
                self.base.cam,
                sensitivity=40.0,
                collision_traverser=collision_traverser,
                render_node=render_node,
                side_offset=0.5  # Reduced for better combat framing
            ),
        }
        
        # Initialize CameraState component if not exists
        camera_state = world.get_component(player_id, CameraState)
        if not camera_state:
            camera_state = CameraState(
                mode=CameraMode.EXPLORATION,
                yaw=0.0,
                pitch=-15.0,  # Looking down slightly
                distance=5.0,
                current_distance=5.0,
                auto_center_strength=0.3  # Gentle auto-center by default
            )
            world.add_component(player_id, camera_state)
        
        # Set active camera
        self._switch_to_mode(camera_state.mode, camera_state)
        
        self.base.cam.setHpr(0, 0, 0)
        print(f"📷 Camera initialized in {camera_state.mode.name} mode")
        print(f"   - Available modes: {list(self.cameras.keys())}")
        print(f"   - Active camera: {self.active_camera.__class__.__name__}")
        print(f"   - Collision detection: {'enabled' if collision_traverser else 'disabled'}")
        print(f"   - Side offset: {side_offset}")
    
    def update(self, ctx: PlayerContext) -> None:
        # Get camera state from ECS
        camera_state = ctx.world.get_component(ctx.player_id, CameraState)
        if not camera_state:
            return
        
        # Handle toggle cooldown
        camera_state.toggle_cooldown = max(0, camera_state.toggle_cooldown - ctx.dt)
        
        # Handle camera mode toggle (V key)
        if ctx.input.is_action_active(InputAction.CAMERA_TOGGLE_MODE) and camera_state.toggle_cooldown <= 0:
            print(f"🔄 Toggling camera mode from {camera_state.mode.name}")
            self._toggle_camera_mode(camera_state)
            camera_state.toggle_cooldown = 0.3
            print(f"   → New mode: {camera_state.mode.name}")
        
        # Check for mode changes (can be triggered by game state)
        if self.active_camera != self.cameras.get(camera_state.mode):
            self._switch_to_mode(camera_state.mode, camera_state)
        
        # Handle scroll wheel zoom (exploration and combat modes only)
        if camera_state.mode in (CameraMode.EXPLORATION, CameraMode.COMBAT):
            scroll = ctx.input.scroll_delta
            if scroll != 0:
                zoom_speed = 0.5  # Distance change per scroll notch
                new_distance = camera_state.distance - (scroll * zoom_speed)
                
                # Get the active camera and update distance
                active_cam = self.cameras.get(camera_state.mode)
                if hasattr(active_cam, 'set_distance'):
                    active_cam.set_distance(camera_state, new_distance)
        
        # Update settings from config if available
        if hasattr(self.base, 'config_manager') and self.base.config_manager:
            sensitivity = self.base.config_manager.get("mouse_sensitivity", 40.0)
            fov = self.base.config_manager.get("fov", 90.0)
            
            # Apply FOV
            self.base.camLens.setFov(fov)
            
            # Apply sensitivity to all cameras
            for camera in self.cameras.values():
                if hasattr(camera, 'set_sensitivity'):
                    camera.set_sensitivity(sensitivity)
            
            # Apply camera distance (exploration/combat only)
            cam_dist = self.base.config_manager.get("camera_distance", 4.0)
            for mode in (CameraMode.EXPLORATION, CameraMode.COMBAT):
                cam = self.cameras.get(mode)
                if cam and hasattr(cam, 'set_distance'):
                    cam.set_distance(camera_state, cam_dist)
            
            # Apply camera side offset (exploration/combat only)
            side_offset = self.base.config_manager.get("camera_side_offset", 1.0)
            for mode in (CameraMode.EXPLORATION, CameraMode.COMBAT):
                cam = self.cameras.get(mode)
                if cam and hasattr(cam, 'side_offset'):
                    cam.side_offset = side_offset
            
            # Apply auto-center strength
            auto_center = self.base.config_manager.get("camera_auto_center_strength", 0.3)
            camera_state.auto_center_strength = auto_center
        
        # Build camera update context
        player_velocity = LVector3f(ctx.state.velocity_x, 
                                    ctx.state.velocity_y, 
                                    ctx.state.velocity_z)
        
        cam_ctx = CameraUpdateContext(
            camera_node=self.base.cam,
            camera_state=camera_state,
            target_position=ctx.transform.position,
            player_velocity=player_velocity,
            mouse_delta=ctx.input.mouse_delta,
            dt=ctx.dt,
            world=ctx.world,
            collision_traverser=getattr(ctx.world, 'collision_traverser', None),
            render_node=self.base.render
        )
        
        # Update active camera
        if self.active_camera:
            self.active_camera.update(cam_ctx)
    
    def _switch_to_mode(self, mode: CameraMode, camera_state: CameraState):
        """Switch to a different camera mode.
        
        Args:
            mode: Target camera mode
            camera_state: CameraState component
        """
        # Exit old camera
        if self.active_camera:
            self.active_camera.on_exit(camera_state)
        
        # Enter new camera
        self.active_camera = self.cameras.get(mode)
        if self.active_camera:
            self.active_camera.on_enter(camera_state)
            print(f"📷 Switched to {mode.name} ({self.active_camera.__class__.__name__})")
    
    def _toggle_camera_mode(self, camera_state: CameraState):
        """Toggle between first-person and exploration modes.
        
        Args:
            camera_state: CameraState component
        """
        if camera_state.mode == CameraMode.FIRST_PERSON:
            camera_state.mode = CameraMode.EXPLORATION
        else:
            camera_state.mode = CameraMode.FIRST_PERSON
