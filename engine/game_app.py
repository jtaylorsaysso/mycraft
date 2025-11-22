from ursina import Ursina

from engine.world import World
from engine.player import Player

def run():
    app = Ursina()

    # Create the world (flat field for MVP)
    world = World()
    player = Player(start_pos=(10,2,10))

    app.run()