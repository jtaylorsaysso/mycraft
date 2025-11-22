from ursina import Entity, camera, color
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
        # Create a camera pivot that rotates with the player
        self.camera_pivot = Entity(parent=self)
        
        # Position camera behind and above the player (over-the-shoulder view)
        camera.position = (0, 5, -10)  # 2 units up, 5 units behind
        camera.parent = self.camera_pivot
        
        # Make camera look at the player
        camera.look_at(self)
        
    def input(self, key):
        """Delegate input handling to InputHandler"""
        self.input_handler.input(key)
        
    def update(self):
        """Delegate update logic to InputHandler"""
        from ursina import time
        dt = time.dt
        self.input_handler.update(dt)

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