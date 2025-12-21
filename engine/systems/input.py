"""Player control system using native Panda3D InputManager and MyCraft Physics."""

from engine.ecs.system import System
from engine.input.manager import InputManager
from engine.rendering.camera import FPSCamera
from engine.components.core import Transform
from engine.physics import (
    KinematicState,
    integrate_movement,
    apply_gravity,
    perform_jump,
    register_jump_press,
    can_consume_jump,
    update_timers
)
from panda3d.core import LVector3f
import math

class PlayerControlSystem(System):
    """System that handles player movement and camera controls with physics."""
    
    # Physics Constants
    MOVE_SPEED = 6.0
    RUN_SPEED = 10.0
    JUMP_HEIGHT = 1.2
    GRAVITY = -20.0  # Snappy gravity
    
    # Water Physics Constants
    WATER_MOVE_SPEED = 4.0
    WATER_GRAVITY = -2.0      # Very low gravity in water
    WATER_BUOYANCY = 15.0     # Upward force when submerged
    WATER_DRAG = 2.0          # High drag in water
    SWIM_SPEED = 3.0          # Vertical swim speed
    
    def __init__(self, world, event_bus, base):
        super().__init__(world, event_bus)
        self.base = base
        # Allow passing base later if needed, but InputManager needs it
        self.input = InputManager(base)
        self.camera_controller = None
        
        # Track physics state for entities
        # entity_id -> KinematicState
        self.physics_states = {}
        
    def initialize(self):
        """Setup camera when system is added."""
        # Find player entity
        player_id = self.world.get_entity_by_tag("player")
        if player_id:
            # Setup FPS camera
            self.camera_controller = FPSCamera(self.base.cam, player_entity=None, sensitivity=40.0)
            
            # Set initial camera orientation
            self.base.cam.setHpr(0, 0, 0)
            
            self.input.lock_mouse()

    def update(self, dt: float):
        """Process input and update player transform."""
        self.input.update()
        
        player_id = self.world.get_entity_by_tag("player")
        if not player_id:
            return
            
        transform = self.world.get_component(player_id, Transform)
        if not transform:
            return

        # Ensure we have physics state
        if player_id not in self.physics_states:
            self.physics_states[player_id] = KinematicState()
        
        state = self.physics_states[player_id]
        
        # 1. Update Camera
        if self.camera_controller:
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
        target_speed = self.MOVE_SPEED
        if in_water:
            target_speed = self.WATER_MOVE_SPEED
            
        target_vel = move_dir * target_speed
        
        # Apply reduced control/friction
        if in_water:
            # Water resistance/drag
            # Drag opposes velocity
            drag = self.WATER_DRAG * dt
            # Simple linear interpolation towards target velocity
            state.velocity_x += (target_vel.x - state.velocity_x) * drag
            state.velocity_z += (target_vel.z - state.velocity_z) * drag
        else:
            # Snappy ground movement
            state.velocity_x = target_vel.x
            state.velocity_z = target_vel.z

        # -- VERTICAL --
        jump_requested = self.input.is_key_down('space')
        
        if jump_requested:
            register_jump_press(state)

        if in_water:
            # Swimming logic
            # Apply buoyancy
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
        
        # Override ground check to handle coordinate mapping
        def remapped_ground_check(entity):
            # Input is wrapper.
            # entity.x -> Panda X
            # entity.z -> Panda Y (World Depth)
            if terrain_system:
                # TerrainSystem uses (x, z) where z is depth/forward
                h = terrain_system.get_height(entity.x, entity.z) 
                return h
            return 0.0

        integrate_movement(
            wrapper,
            state,
            dt,
            ground_check=remapped_ground_check
        )
        
        update_timers(state, dt)

        # Update camera position to follow player
        cam_offset = LVector3f(0, 0, 1.8)
        self.base.cam.setPos(transform.position + cam_offset)
        
        # Debug toggle
        if self.input.is_key_down('escape'):
            self.input.unlock_mouse()

    def _get_system(self, system_name):
        """Helper to look up a sibling system."""
        if hasattr(self.world, '_systems'):
             for sys in self.world._systems:
                 if sys.__class__.__name__ == system_name:
                     return sys
        return None
