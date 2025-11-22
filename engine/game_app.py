from ursina import Ursina

from engine.world import World
from engine.player import Player
from network.client import get_client

def run(networking: bool = False):
    app = Ursina()

    # Create the world (flat field for MVP)
    world = World()
    
    # Get spawn position from server if connected
    client = get_client()
    if networking and client and client.is_connected():
        # Use server-provided spawn position
        spawn_pos = tuple(client.player_id and [10, 2, 10] or [10, 2, 10])  # TODO: Get from welcome message
    else:
        spawn_pos = (10, 2, 10)
    
    player = Player(start_pos=spawn_pos, networking=networking)

    app.run()