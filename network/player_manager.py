import time
from typing import Dict, List, Optional

class PlayerManager:
    """Manages player states and identification."""
    
    def __init__(self):
        self.player_states: Dict[str, Dict] = {}
        self.next_player_id = 1
        self.host_player_id = "host_player"
        
        # Initialize host player
        self.player_states[self.host_player_id] = {
            "pos": [10, 2, 10],
            "rot_y": 0,
            "last_update": time.time(),
            "is_host": True,
        }

    def generate_player_id(self) -> str:
        """Generate and return a new unique player ID."""
        pid = f"player_{self.next_player_id}"
        self.next_player_id += 1
        return pid

    def add_player(self, player_id: str) -> None:
        """Initialize state for a new player."""
        self.player_states[player_id] = {
            "pos": [10, 2, 10],  # Default spawn
            "rot_y": 0,
            "last_update": time.time()
        }

    def remove_player(self, player_id: str) -> None:
        """Remove a player's state."""
        if player_id == self.host_player_id:
            return
        if player_id in self.player_states:
            del self.player_states[player_id]

    def update_player_state(self, player_id: str, pos: List[float], rot_y: float) -> None:
        """Update position and rotation for a player."""
        if player_id in self.player_states:
            self.player_states[player_id].update({
                "pos": pos,
                "rot_y": rot_y,
                "last_update": time.time()
            })

    def get_player_state(self, player_id: str) -> Optional[Dict]:
        """Get the state dictionary for a player."""
        return self.player_states.get(player_id)

    def get_all_players(self) -> Dict[str, Dict]:
        """Return a snapshot of all player states."""
        return dict(self.player_states)

    def set_host_position(self, x: float, y: float, z: float) -> None:
        """Move the host player."""
        state = self.player_states.get(self.host_player_id)
        if state:
            state["pos"] = [float(x), float(y), float(z)]
            state["last_update"] = time.time()

    def set_host_rotation(self, rot_y: float) -> None:
        """Rotate the host player."""
        state = self.player_states.get(self.host_player_id)
        if state:
            state["rot_y"] = float(rot_y)
            state["last_update"] = time.time()
