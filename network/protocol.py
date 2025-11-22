"""
MyCraft Network Protocol

Defines the message format for LAN multiplayer communication.
All messages are JSON objects ending with newline character.

Message Types:
- welcome: Server assigns player ID and spawn position
- state_update: Client sends position/rotation to server
- state_snapshot: Server broadcasts all player states
- player_join: Server notifies when new player joins
- player_leave: Server notifies when player disconnects
"""

from typing import Dict, List, Any, Optional
import json
import time

# Message type constants
WELCOME = "welcome"
STATE_UPDATE = "state_update"
STATE_SNAPSHOT = "state_snapshot"
PLAYER_JOIN = "player_join"
PLAYER_LEAVE = "player_leave"

# Network settings
DEFAULT_PORT = 5420
SERVER_TICK_RATE = 20  # Hz
CLIENT_SEND_RATE = 10  # Hz
TIMEOUT_SECONDS = 5.0


def create_welcome(player_id: str, spawn_pos: List[float]) -> str:
    """Create welcome message for new player."""
    return json.dumps({
        "type": WELCOME,
        "player_id": player_id,
        "spawn_pos": spawn_pos
    }) + "\n"


def create_state_update(pos: List[float], rot_y: float) -> str:
    """Create state update message from client to server."""
    return json.dumps({
        "type": STATE_UPDATE,
        "pos": pos,
        "rot_y": rot_y
    }) + "\n"


def create_state_snapshot(players: Dict[str, Dict]) -> str:
    """Create state snapshot message from server to clients."""
    return json.dumps({
        "type": STATE_SNAPSHOT,
        "players": players,
        "timestamp": time.time()
    }) + "\n"


def create_player_join(player_id: str) -> str:
    """Create player join notification."""
    return json.dumps({
        "type": PLAYER_JOIN,
        "player_id": player_id
    }) + "\n"


def create_player_leave(player_id: str) -> str:
    """Create player leave notification."""
    return json.dumps({
        "type": PLAYER_LEAVE,
        "player_id": player_id
    }) + "\n"


def parse_message(data: str) -> Optional[Dict[str, Any]]:
    """Parse incoming message and validate format."""
    try:
        message = json.loads(data.strip())
        msg_type = message.get("type")
        
        if msg_type in [WELCOME, STATE_UPDATE, STATE_SNAPSHOT, PLAYER_JOIN, PLAYER_LEAVE]:
            return message
        else:
            print(f"Unknown message type: {msg_type}")
            return None
            
    except json.JSONDecodeError as e:
        print(f"Invalid JSON message: {e}")
        return None


# Message validation schemas
WELCOME_SCHEMA = {
    "type": WELCOME,
    "player_id": str,
    "spawn_pos": List[float]
}

STATE_UPDATE_SCHEMA = {
    "type": STATE_UPDATE,
    "pos": List[float],
    "rot_y": float
}

STATE_SNAPSHOT_SCHEMA = {
    "type": STATE_SNAPSHOT,
    "players": Dict[str, Dict],
    "timestamp": float
}

PLAYER_EVENT_SCHEMA = {
    "type": str,
    "player_id": str
}