from ursina import Entity, load_model, color
class World:
    def __init__(self):
        self.generate_flat_field()

    @staticmethod
    def generate_flat_field():
        size = 20

        for x in range(size):
            for z in range(size):
                Entity(
                    model = 'cube',
                    texture = 'grass',
                    position = (x, 1, z),
                    scale = 1
                )