from ursina import Entity, color, Vec3, lerp, time, Text
from games.voxel_world.components.animation import AnimatedMannequin, AnimationController


class RemotePlayer(Entity):
    """
    Represents a remote player in the world.
    Handles visual representation (animated mannequin) and position smoothing (interpolation).
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create animated mannequin (Azure to distinguish from local player)
        self.mannequin = AnimatedMannequin(parent=self, body_color=color.azure)
        self.animation_controller = AnimationController(self.mannequin)
        
        # Name tag (floating text above head)
        self.name_tag = Text(
            parent=self,
            text='Unknown',
            y=2.2,
            scale=5,
            color=color.white,
            billboard=True,
            origin=(0, 0),
            background=True
        )
        self.name_tag.background.color = color.rgba(0, 0, 0, 100)
        
        # Interpolation state
        self.target_position = self.position
        self.target_rotation = self.rotation_y
        self.lerp_speed = 10.0  # Speed of interpolation
        
        # Velocity estimation for animations
        self._last_position = Vec3(self.position.x, self.position.y, self.position.z)
        self._estimated_velocity = Vec3(0, 0, 0)

    def set_name(self, name: str):
        """Update the player's name tag."""
        if self.name_tag.text != name:
            self.name_tag.text = name

    def set_target(self, pos, rot_y):
        """Update the target position and rotation."""
        self.target_position = Vec3(*pos)
        self.target_rotation = rot_y
        
        # Teleport if too far (e.g. respawn or initial join)
        if (self.target_position - self.position).length() > 5:
            self.position = self.target_position
            self.rotation_y = self.target_rotation
            self._last_position = Vec3(self.position.x, self.position.y, self.position.z)
            self._estimated_velocity = Vec3(0, 0, 0)

    def update(self):
        """Called every frame by Ursina."""
        dt = time.dt
        
        # Estimate velocity from position change (for animations)
        if dt > 0:
            self._estimated_velocity = (self.target_position - self._last_position) / dt
        self._last_position = Vec3(self.position.x, self.position.y, self.position.z)
        
        # Interpolate position
        self.position = lerp(self.position, self.target_position, dt * self.lerp_speed)
        
        # Interpolate rotation (simple lerp)
        # Note: For full robustness, should use slerp or handle 0-360 wrap, 
        # but simple lerp is okay for limited Y-rotation in this prototype
        self.rotation_y = lerp(self.rotation_y, self.target_rotation, dt * self.lerp_speed)
        
        # Update animations based on estimated velocity
        # Assume grounded since we don't have physics state for remote players
        grounded = abs(self._estimated_velocity.y) < 0.5
        self.animation_controller.update(dt, self._estimated_velocity, grounded)
