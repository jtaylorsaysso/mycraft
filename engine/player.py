from ursina import Entity, camera, color, Vec3, raycast
from engine.input_handler import InputHandler

class Player(Entity):
    def __init__(self, start_pos=(0,2,0)):
        # Player parent entity
        super().__init__(
            position=start_pos
        )

        # Basic mannequin: 3 stacked cubes
        self.build_body()

        # Setup third-person camera
        self.setup_third_person_camera()
        
        # Initialize input handler
        self.input_handler = InputHandler(self)
        
    def setup_third_person_camera(self):
        """Create an over-the-shoulder third-person camera setup"""
        # Create a camera pivot at torso height (center of player)
        self.camera_pivot = Entity(parent=self, y=1.0)
        
        # Camera offset: right, up, back (so player appears on left side)
        self.camera_offset = Vec3(1, 2, -4)
        
        # Camera settings
        camera.parent = self.camera_pivot
        camera.position = self.camera_offset
        camera.fov = 60  # Field of view
        
        # Look ahead in facing direction
        target = self.camera_pivot.world_position + self.forward * 3
        camera.look_at(target)
        
        # Camera collision prevention settings
        self.min_camera_distance = 1.0
        self.camera_safety_margin = 0.1
        
    def input(self, key):
        """Delegate input handling to InputHandler"""
        self.input_handler.input(key)
        
    def update(self):
        """Delegate update logic to InputHandler and update camera"""
        from ursina import time
        dt = time.dt
        self.input_handler.update(dt)
        self.update_camera()
    
    def update_camera(self):
        """Update camera position with collision prevention"""
        # Calculate desired world position
        desired_world_pos = (
            self.camera_pivot.world_position +
            self.camera_pivot.right * self.camera_offset.x +
            self.camera_pivot.up * self.camera_offset.y +
            self.camera_pivot.back * abs(self.camera_offset.z)
        )
        
        # Raycast from pivot to desired position
        origin = self.camera_pivot.world_position
        direction = (desired_world_pos - origin).normalized()
        distance = (desired_world_pos - origin).length()
        
        # Check for collisions (ignore player and its parts)
        hit_info = raycast(origin, direction, distance=distance, ignore=[self])
        
        if hit_info.hit:
            # Clamp camera to safe distance before obstacle
            clamped_dist = max(self.min_camera_distance, hit_info.distance - self.camera_safety_margin)
            camera.world_position = origin + direction * clamped_dist
        else:
            # Use desired position
            camera.world_position = desired_world_pos
        
        # Always look ahead in facing direction
        target = self.camera_pivot.world_position + self.forward * 3
        camera.look_at(target)

    def build_body(self):
        # Head
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(150, 125, 100),
            scale=0.3,
            y=1.6
        )

        #Torso
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(150, 125, 100),
            scale=(0.3, 1.2, 0.4),
            y=0.9

        )

        #Legs
        Entity(
            parent=self,
            model='cube',
            color=color.rgb(150, 125, 100),
            scale=(0.3, 1, 0.4),
            y=0.3
        )