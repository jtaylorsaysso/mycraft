"""
Remote Player Manager System

Manages visual representation of remote players using RemotePlayer.
Creates, updates, and destroys remote players based on network state.
"""

from engine.ecs.system import System
from engine.networking.remote_player import RemotePlayer
from engine.networking.client import get_client
from typing import Dict, Optional


class RemotePlayerManager(System):
    """Manages remote player instances for multiplayer."""
    
    def __init__(self, world, event_bus, base):
        super().__init__(world, event_bus)
        self.base = base
        
        # Track RemotePlayer instances for each remote player
        # player_id -> RemotePlayer instance
        self.remote_players: Dict[str, RemotePlayer] = {}
    
    def get_dependencies(self) -> list:
        """RemotePlayerManager has no hard dependencies.
        
        It gracefully handles the case where no network client exists.
        Returns empty list to indicate it's always ready.
        """
        return []
        
    def update(self, dt: float):
        """Update remote players based on network state."""
        client = get_client()
        if not client or not client.is_connected():
            return
        
        # Get current remote players from network client
        remote_players_data = client.get_remote_players()
        
        # Remove players who left
        for player_id in list(self.remote_players.keys()):
            if player_id not in remote_players_data:
                self._remove_player(player_id)
        
        # Create or update players
        for player_id, player_data in remote_players_data.items():
            if player_id not in self.remote_players:
                self._create_player(player_id, player_data)
            else:
                self._update_player(player_id, player_data, dt)
    
    def _create_player(self, player_id: str, player_data: Dict):
        """Create a new remote player.
        
        Args:
            player_id: Unique player identifier
            player_data: Player state data from server
        """
        # Get player name from data
        player_name = player_data.get("name", "Unknown")
        
        # Create RemotePlayer instance (includes mannequin and name tag)
        remote_player = RemotePlayer(
            parent_node=self.base.render,
            player_id=player_id,
            name=player_name
        )
        
        # Set initial position and rotation
        pos = player_data.get("pos", [0, 0, 0])
        rot_y = player_data.get("rot_y", 0)
        remote_player.set_target(tuple(pos), rot_y)
        
        self.remote_players[player_id] = remote_player
        print(f"✨ Created remote player {player_id} ({player_name})")
    
    def _update_player(self, player_id: str, player_data: Dict, dt: float):
        """Update an existing remote player.
        
        Args:
            player_id: Unique player identifier
            player_data: Player state data from server
            dt: Delta time since last update
        """
        remote_player = self.remote_players[player_id]
        
        # Update name if changed
        player_name = player_data.get("name", "Unknown")
        if remote_player.name != player_name:
            remote_player.set_name(player_name)
        
        # Update position and rotation
        pos = player_data.get("pos", [0, 0, 0])
        rot_y = player_data.get("rot_y", 0)
        remote_player.set_target(tuple(pos), rot_y)
        
        # Update animations and interpolation
        remote_player.update(dt)
    
    def _remove_player(self, player_id: str):
        """Remove a remote player when they disconnect.
        
        Args:
            player_id: Unique player identifier
        """
        if player_id in self.remote_players:
            remote_player = self.remote_players[player_id]
            remote_player.cleanup()
            del self.remote_players[player_id]
            print(f"👋 Removed remote player {player_id}")
    
    def cleanup(self):
        """Clean up all remote players."""
        for player_id in list(self.remote_players.keys()):
            self._remove_player(player_id)
