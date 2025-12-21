"""
Remote Player Rendering - Panda3D Native

Represents a remote player in the world using Panda3D NodePath hierarchy.
Handles visual representation (animated mannequin) and position smoothing (interpolation).
"""

from panda3d.core import NodePath, LVector3f
from engine.animation.mannequin import AnimatedMannequin, AnimationController
from engine.ui.name_tag import NameTag
from typing import Optional


class RemotePlayer:
    """
    Represents a remote player in the world.
    Handles visual representation (animated mannequin) and position smoothing (interpolation).
    """
    
    def __init__(self, parent_node: NodePath, player_id: str, name: str = "Unknown"):
        """Initialize remote player.
        
        Args:
            parent_node: Panda3D NodePath to attach player to (usually render)
            player_id: Unique identifier for this player
            name: Player's display name
        """
        self.player_id = player_id
        self.root = parent_node.attachNewNode(f"remote_player_{player_id}")
        
        # Create animated mannequin (Azure/blue to distinguish from local player)
        self.mannequin = AnimatedMannequin(self.root, body_color=(0.2, 0.5, 1.0, 1.0))
        self.animation_controller = AnimationController(self.mannequin)
        
        # Create 3D billboarded name tag
        self.name = name
        self.name_tag = NameTag(self.root, name)
        
        # Interpolation state
        self.target_position = LVector3f(0, 0, 0)
        self.target_rotation_y = 0.0
        self.lerp_speed = 10.0  # Speed of interpolation
        
        # Velocity estimation for animations
        self._last_position = LVector3f(0, 0, 0)
        self._estimated_velocity = LVector3f(0, 0, 0)
    
    def set_name(self, name: str):
        """Update the player's name tag.
        
        Args:
            name: New display name
        """
        if self.name != name:
            self.name = name
            self.name_tag.set_name(name)
    
    def set_target(self, pos: tuple, rot_y: float):
        """Update the target position and rotation.
        
        Args:
            pos: Target position (x, y, z)
            rot_y: Target Y rotation in degrees
        """
        self.target_position = LVector3f(*pos)
        self.target_rotation_y = rot_y
        
        # Teleport if too far (e.g. respawn or initial join)
        current_pos = self.root.getPos()
        distance = (self.target_position - current_pos).length()
        if distance > 5:
            self.root.setPos(self.target_position)
            self.root.setH(self.target_rotation_y)
            self._last_position = LVector3f(self.target_position)
            self._estimated_velocity = LVector3f(0, 0, 0)
    
    def update(self, dt: float):
        """Update interpolation and animations.
        
        Args:
            dt: Delta time since last frame
        """
        # Estimate velocity from position change (for animations)
        if dt > 0:
            current_pos = self.root.getPos()
            self._estimated_velocity = (self.target_position - self._last_position) / dt
            self._last_position = LVector3f(current_pos)
        
        # Interpolate position (lerp)
        current_pos = self.root.getPos()
        new_pos = current_pos + (self.target_position - current_pos) * (dt * self.lerp_speed)
        self.root.setPos(new_pos)
        
        # Interpolate rotation (simple lerp for Y-axis)
        # Note: For full robustness, should handle 0-360 wrap
        current_h = self.root.getH()
        angle_diff = self.target_rotation_y - current_h
        
        # Normalize angle difference to [-180, 180]
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        
        new_h = current_h + angle_diff * (dt * self.lerp_speed)
        self.root.setH(new_h)
        
        # Update animations based on estimated velocity
        # Assume grounded since we don't have physics state for remote players
        grounded = abs(self._estimated_velocity.z) < 0.5  # Z is up in Panda3D
        self.animation_controller.update(dt, self._estimated_velocity, grounded)
    
    def cleanup(self):
        """Remove player from scene."""
        self.name_tag.cleanup()
        self.mannequin.cleanup()
        self.root.removeNode()
