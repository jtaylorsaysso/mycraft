"""Player control system using native Panda3D InputManager and MyCraft Physics."""

from engine.ecs.system import System
from engine.input.manager import InputManager
from engine.rendering.camera import FPSCamera, ThirdPersonCamera
from engine.components.core import Transform
from engine.physics import (
    KinematicState,
    integrate_movement,
    apply_gravity,
    perform_jump,
    register_jump_press,
    can_consume_jump,
    update_timers,
    apply_horizontal_acceleration,
    apply_slope_forces
)
from engine.physics.constants import (
    MOVE_SPEED,
    ACCELERATION,
    FRICTION,
    AIR_CONTROL,
    WATER_MULTIPLIER,
    WATER_DRAG
)
from panda3d.core import LVector3f
import math

class PlayerControlSystem(System):
    """System that handles player movement and camera controls with physics."""
    
    # Removed hardcoded constants - using engine.physics.constants
    
    # Keeping these for now as they might be specific to player or not yet in shared constants
    RUN_SPEED = 10.0
    JUMP_HEIGHT = 1.2
    GRAVITY = -20.0  # Snappy gravity
    
    # Water Physics Constants (Player specific)
    WATER_GRAVITY = -2.0      # Very low gravity in water
    WATER_BUOYANCY = 15.0     # Upward force when submerged
    SWIM_SPEED = 3.0          # Vertical swim speed
    
    def __init__(self, world, event_bus, base):
        super().__init__(world, event_bus)
        from engine.core.logger import get_logger
        self.logger = get_logger("systems.player_control")
        
        self.base = base
        self.input = None  # Created in initialize()
        self.camera_controller = None
        self.fps_camera = None
        self.third_person_camera = None
        
        # Camera mode: 'third_person' or 'first_person'
        self.camera_mode = 'third_person'  # Default to third-person
        self.camera_toggle_cooldown = 0.0  # Prevent rapid toggling
        
        # Local player visual representation
        self.local_mannequin = None
        self.local_animation_controller = None
        
        # Track physics state for entities
        # entity_id -> KinematicState
        self.physics_states = {}
        
        # Create collision traverser for physics raycasting
        from panda3d.core import CollisionTraverser
        self.collision_traverser = CollisionTraverser('player_physics')

    def get_dependencies(self) -> list:
        """PlayerControlSystem requires a player entity to function."""
        return ["player"]
        
    def initialize(self):
        """Phase 2: Setup input manager (no player needed yet)."""
        # Create input manager but DON'T lock mouse yet
        self.input = InputManager(self.base)
        self.logger.info("Input manager initialized (waiting for player)")

    def on_ready(self):
        """Phase 3: Called when player entity exists - setup camera and controls."""
        super().on_ready()
        
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            self.logger.error("on_ready called but player entity not found!")
            return
            
        transform = self.world.get_component(player_id, Transform)
        if not transform:
            self.logger.error(f"Player {player_id} has no Transform component!")
            return
            
        # Create local player mannequin
        from engine.animation.mannequin import AnimatedMannequin, AnimationController
        self.local_mannequin = AnimatedMannequin(
            self.base.render, 
            body_color=(0.4, 0.8, 0.4, 1.0)  # Green for local player
        )
        self.local_mannequin.root.setPos(transform.position)
        self.local_animation_controller = AnimationController(self.local_mannequin)
        
        # Setup both camera modes
        self.fps_camera = FPSCamera(self.base.cam, None, sensitivity=40.0)
        self.third_person_camera = ThirdPersonCamera(self.base.cam, None, sensitivity=40.0)
        
        # Set active camera based on mode
        if self.camera_mode == 'third_person':
            self.camera_controller = self.third_person_camera
            self.local_mannequin.root.show()
        else:
            self.camera_controller = self.fps_camera
            self.local_mannequin.root.hide()
        
        # Set initial camera orientation
        self.base.cam.setHpr(0, 0, 0)
        
        # NOW lock the mouse (player is ready)
        self.input.lock_mouse()
        
        self.logger.info(f"Player controls ready for player {player_id}")


    def update(self, dt: float):
        """Process input and update player transform."""
        # System only updates when ready (player exists)
        self.input.update()
        
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            # Player disappeared - this shouldn't happen if dependencies work correctly
            self.logger.warning("Player entity disappeared during update!")
            return

            
        transform = self.world.get_component(player_id, Transform)
        if not transform:
            return

        # Ensure we have physics state
        if player_id not in self.physics_states:
            self.physics_states[player_id] = KinematicState()
        
        state = self.physics_states[player_id]
        
        # Update spawn protection timer
        from engine.components.core import Health
        health = self.world.get_component(player_id, Health)
        if health and health.invulnerable and health.invuln_timer > 0:
            health.invuln_timer -= dt
            if health.invuln_timer <= 0:
                health.invulnerable = False
                health.invuln_timer = 0.0
                print("🛡️ Spawn protection expired")
        
        # Handle camera mode toggle (V key)

        self.camera_toggle_cooldown = max(0, self.camera_toggle_cooldown - dt)
        if self.input.is_key_down('v') and self.camera_toggle_cooldown <= 0:
            self._toggle_camera_mode()
            self.camera_toggle_cooldown = 0.3  # 300ms cooldown
        
        # 1. Update Camera
        if self.camera_controller:
            if self.camera_mode == 'third_person':
                # Third-person camera needs target position
                self.camera_controller.update(
                    self.input.mouse_delta[0],
                    self.input.mouse_delta[1],
                    dt,
                    transform.position
                )
            else:
                # FPS camera
                self.camera_controller.update(
                    self.input.mouse_delta[0],
                    self.input.mouse_delta[1],
                    dt
                )

        # 2. Check Environment (Water & Ground)
        in_water = False
        submersion = 0.0
        
        water_system = self._get_system("WaterPhysicsSystem")
        if water_system:
            in_water = water_system.is_position_in_water(transform.position)
            submersion = water_system.get_submersion_level(transform.position)

        terrain_system = self._get_system("TerrainSystem")
        
        # 3. Handle Input & Movement
        move_dir = LVector3f(0, 0, 0)
        
        # Get forward/right vectors from camera HPR (ignore pitch for movement)
        h = self.base.cam.getH()
        rad = math.radians(h)
        forward = LVector3f(-math.sin(rad), math.cos(rad), 0)
        right = LVector3f(math.cos(rad), math.sin(rad), 0)
        
        if self.input.is_key_down('w'): move_dir += forward
        if self.input.is_key_down('s'): move_dir -= forward
        if self.input.is_key_down('a'): move_dir -= right
        if self.input.is_key_down('d'): move_dir += right
        
        if move_dir.length() > 0:
            move_dir.normalize()
            
        # 4. Apply Physics
        
        # -- HORIZONTAL --
        target_speed = MOVE_SPEED
        if in_water:
            target_speed = MOVE_SPEED * WATER_MULTIPLIER
            
        target_vel = move_dir * target_speed
        
        # Apply unified acceleration model
        apply_horizontal_acceleration(state, (target_vel.x, target_vel.z), dt, state.grounded)

        # Apply water drag if in water
        if in_water:
            # Simple exponential decay of horizontal velocity
            state.velocity_x *= max(0.0, 1 - WATER_DRAG * dt)
            state.velocity_z *= max(0.0, 1 - WATER_DRAG * dt)

        # -- VERTICAL --
        jump_requested = self.input.is_key_down('space')
        if jump_requested:
            register_jump_press(state)
            
        if in_water:
            # Swimming logic
            # Apply buoyancy/water gravity
            apply_gravity(state, dt, gravity=self.WATER_GRAVITY)
            
            # Swim up
            if jump_requested:
                state.velocity_y += self.SWIM_SPEED * dt
                # Cap swim speed
                if state.velocity_y > self.SWIM_SPEED:
                    state.velocity_y = self.SWIM_SPEED
                    
            state.grounded = False # Always floating in water
            
        else:
            # Standard Gravity
            apply_gravity(state, dt, gravity=self.GRAVITY)

            # Apply slope forces if sliding
            apply_slope_forces(state, dt)
            
            # Jumping
            if can_consume_jump(state):
                perform_jump(state, self.JUMP_HEIGHT * -self.GRAVITY * 0.4) # Approx height based on gravity

        # 5. Integrate & Move
        # We wrap transform to match protocol needed by physics (x,y,z properties)
        # Physics Engine Expects: Y=Up, Z=Forward/Back (Ursina legacy)
        # Panda3D Expects: Z=Up, Y=Forward/Back
        # We must bridge this.
        
        class TransformWrapper:
            def __init__(self, t): self.t = t
            @property
            def x(self): return self.t.position.x
            @x.setter
            def x(self, v): self.t.position.x = v
            # Map Physics Y (Up) -> Panda Z (Up)
            @property
            def y(self): return self.t.position.z
            @y.setter
            def y(self, v): self.t.position.z = v
            # Map Physics Z (Depth) -> Panda Y (Depth)
            @property
            def z(self): return self.t.position.y
            @z.setter
            def z(self, v): self.t.position.y = v
            
        wrapper = TransformWrapper(transform)
        
        # Ground check using collision raycast
        def remapped_ground_check(entity):
            from engine.physics import raycast_ground_height
            return raycast_ground_height(
                entity,
                self.collision_traverser,
                self.base.render,  # Pass render node
                max_distance=5.0,
                foot_offset=0.2,
                ray_origin_offset=2.0,
                return_normal=True  # Request surface normal for slope physics
            )
        
        # Wall check using collision raycast
        def wall_check(entity, movement):
            from engine.physics import raycast_wall_check
            return raycast_wall_check(
                entity,
                movement,
                self.collision_traverser,
                self.base.render,  # Pass render node
                distance_buffer=0.5
            )

        integrate_movement(
            wrapper,
            state,
            dt,
            ground_check=remapped_ground_check,
            wall_check=wall_check
        )
        
        update_timers(state, dt)

        # Update local mannequin position and animations
        if self.local_mannequin:
            self.local_mannequin.root.setPos(transform.position)
            
            # Update mannequin rotation to face camera direction (in third-person)
            if self.camera_mode == 'third_person' and self.third_person_camera:
                self.local_mannequin.root.setH(self.third_person_camera.yaw)
            elif self.camera_mode == 'first_person' and self.fps_camera:
                self.local_mannequin.root.setH(self.fps_camera.yaw)
            
            # Update animations based on physics state
            if self.local_animation_controller:
                velocity = LVector3f(state.velocity_x, state.velocity_z, state.velocity_y)
                self.local_animation_controller.update(dt, velocity, state.grounded)
        
        # Update camera position for first-person mode
        if self.camera_mode == 'first_person':
            cam_offset = LVector3f(0, 0, 1.8)
            self.base.cam.setPos(transform.position + cam_offset)
        
        # Debug toggle
        if self.input.is_key_down('escape'):
            self.input.unlock_mouse()
    
    def cleanup(self):
        """Clean up resources when system is removed."""
        # Unlock mouse
        if self.input:
            self.input.unlock_mouse()
        
        # Clean up mannequin
        if self.local_mannequin:
            self.local_mannequin.cleanup()
            self.local_mannequin = None
        
        self.logger.info("PlayerControlSystem cleaned up")

    def _toggle_camera_mode(self):
        """Toggle between first-person and third-person camera."""
        if self.camera_mode == 'third_person':
            self.camera_mode = 'first_person'
            self.camera_controller = self.fps_camera
            if self.local_mannequin:
                self.local_mannequin.root.hide()
            print("📷 Switched to First-Person")
        else:
            self.camera_mode = 'third_person'
            self.camera_controller = self.third_person_camera
            if self.local_mannequin:
                self.local_mannequin.root.show()
            print("📷 Switched to Third-Person")
    
    def _get_system(self, system_name):
        """Helper to look up a sibling system."""
        if hasattr(self.world, '_systems'):
             for sys in self.world._systems:
                 if sys.__class__.__name__ == system_name:
                     return sys
        return None
