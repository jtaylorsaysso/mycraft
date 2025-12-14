from ursina import Entity, color, Vec3, lerp, time

class RemotePlayer(Entity):
    """
    Represents a remote player in the world.
    Handles visual representation (mannequin) and position smoothing (interpolation).
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create body parts (Remote player is Azure to distinguish from local)
        self.body_color = color.azure
        
        # Head
        Entity(
            parent=self,
            model='cube',
            color=self.body_color,
            scale=0.3,
            y=1.6
        )

        # Torso
        Entity(
            parent=self,
            model='cube',
            color=self.body_color,
            scale=(0.3, 1.2, 0.4),
            y=0.9
        )

        # Right Arm
        Entity(
            parent=self,
            model='cube',
            color=self.body_color,
            scale=(0.15, 1.0, 0.15),
            position=(0.25, 0.9, 0)
        )

        # Left Arm
        Entity(
            parent=self,
            model='cube',
            color=self.body_color,
            scale=(0.15, 1.0, 0.15),
            position=(-0.25, 0.9, 0)
        )

        # Legs
        Entity(
            parent=self,
            model='cube',
            color=self.body_color,
            scale=(0.3, 1, 0.4),
            y=0.3
        )
        
        # Interpolation state
        self.target_position = self.position
        self.target_rotation = self.rotation_y
        self.lerp_speed = 10.0  # Speed of interpolation

    def set_target(self, pos, rot_y):
        """Update the target position and rotation."""
        self.target_position = Vec3(*pos)
        self.target_rotation = rot_y
        
        # Teleport if too far (e.g. respawn or initial join)
        if (self.target_position - self.position).length() > 5:
            self.position = self.target_position
            self.rotation_y = self.target_rotation

    def update(self):
        """Called every frame by Ursina."""
        # Interpolate position
        self.position = lerp(self.position, self.target_position, time.dt * self.lerp_speed)
        
        # Interpolate rotation (simple lerp)
        # Note: For full robustness, should use slerp or handle 0-360 wrap, 
        # but simple lerp is okay for limited Y-rotation in this prototype
        self.rotation_y = lerp(self.rotation_y, self.target_rotation, time.dt * self.lerp_speed)
