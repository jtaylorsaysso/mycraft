from ursina import Ursina, camera

from engine.world import World
from engine.player import Player
from network.client import get_client

# Global references for update loop
_world = None
_player = None

def update():
    """Called each frame by Ursina to update game state."""
    global _world, _player
    
    if _world and _player:
        # Update chunk loading/unloading based on player position
        _world.update(_player.position)
        
        # Update chunk visibility based on camera frustum
        _world.set_chunk_visibility(camera, _player.position)

def run(networking: bool = False):
    global _world, _player
    
    app = Ursina()

    # Create the world (now with dynamic chunk loading)
    _world = World()
    
    # Get spawn position from server if connected
    client = get_client()
    if networking and client and client.is_connected():
        # Use server-provided spawn position
        spawn_pos = tuple(client.spawn_pos) if hasattr(client, 'spawn_pos') else (10, 2, 10)
    else:
        spawn_pos = (10, 2, 10)
    
    _player = Player(start_pos=spawn_pos, networking=networking)

    app.run()