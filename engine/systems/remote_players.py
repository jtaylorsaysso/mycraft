"""
Remote Player Manager System

Manages visual representation of remote players using AnimatedMannequin.
Creates, updates, and destroys mannequins based on network state.
"""

from engine.ecs.system import System
from engine.animation.mannequin import AnimatedMannequin, AnimationController
from engine.networking.client import get_client
from panda3d.core import LVector3f
from typing import Dict, Optional


class RemotePlayerManager(System):
    """Manages remote player mannequins for multiplayer."""
    
    def __init__(self, world, event_bus, base):
        super().__init__(world, event_bus)
        self.base = base
        
        # Track mannequins for each remote player
        # player_id -> {"mannequin": AnimatedMannequin, "controller": AnimationController}
        self.remote_mannequins: Dict[str, Dict] = {}
    
    def get_dependencies(self) -> list:
        """RemotePlayerManager has no hard dependencies.
        
        It gracefully handles the case where no network client exists.
        Returns empty list to indicate it's always ready.
        """
        return []
        
    def update(self, dt: float):
        """Update remote player mannequins based on network state."""
        client = get_client()
        if not client or not client.is_connected():
            return
        
        # Get current remote players from network client
        remote_players = client.get_remote_players()
        
        # Remove mannequins for players who left
        for player_id in list(self.remote_mannequins.keys()):
            if player_id not in remote_players:
                self._remove_mannequin(player_id)
        
        # Create or update mannequins for active players
        for player_id, player_data in remote_players.items():
            if player_id not in self.remote_mannequins:
                self._create_mannequin(player_id, player_data)
            else:
                self._update_mannequin(player_id, player_data, dt)
    
    def _create_mannequin(self, player_id: str, player_data: Dict):
        """Create a new mannequin for a remote player."""
        # Azure/blue color for remote players
        mannequin = AnimatedMannequin(
            self.base.render,
            body_color=(0.2, 0.5, 1.0, 1.0)
        )
        
        # Set initial position
        pos = player_data.get("pos", [0, 0, 0])
        mannequin.root.setPos(LVector3f(*pos))
        
        # Set initial rotation
        rot_y = player_data.get("rot_y", 0)
        mannequin.root.setH(rot_y)
        
        # Create animation controller
        controller = AnimationController(mannequin)
        
        self.remote_mannequins[player_id] = {
            "mannequin": mannequin,
            "controller": controller,
            "last_pos": LVector3f(*pos)
        }
        
        print(f"✨ Created mannequin for player {player_id}")
    
    def _update_mannequin(self, player_id: str, player_data: Dict, dt: float):
        """Update an existing mannequin's position and animation."""
        mannequin_data = self.remote_mannequins[player_id]
        mannequin = mannequin_data["mannequin"]
        controller = mannequin_data["controller"]
        
        # Update position
        pos = player_data.get("pos", [0, 0, 0])
        new_pos = LVector3f(*pos)
        mannequin.root.setPos(new_pos)
        
        # Update rotation
        rot_y = player_data.get("rot_y", 0)
        mannequin.root.setH(rot_y)
        
        # Estimate velocity for animations (from position delta)
        last_pos = mannequin_data.get("last_pos", new_pos)
        if dt > 0:
            velocity = (new_pos - last_pos) / dt
        else:
            velocity = LVector3f(0, 0, 0)
        
        mannequin_data["last_pos"] = LVector3f(new_pos)
        
        # Update animations
        # Assume grounded for now (could be sent from server in future)
        grounded = abs(velocity.z) < 0.5
        controller.update(dt, velocity, grounded)
    
    def _remove_mannequin(self, player_id: str):
        """Remove a mannequin when player disconnects."""
        if player_id in self.remote_mannequins:
            mannequin_data = self.remote_mannequins[player_id]
            mannequin_data["mannequin"].cleanup()
            del self.remote_mannequins[player_id]
            print(f"👋 Removed mannequin for player {player_id}")
    
    def cleanup(self):
        """Clean up all mannequins."""
        for player_id in list(self.remote_mannequins.keys()):
            self._remove_mannequin(player_id)
