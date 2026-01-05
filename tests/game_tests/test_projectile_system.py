
import pytest
from engine.ecs.world import World
from engine.ecs.events import EventBus
from engine.components.core import Transform, Health
from engine.components.projectile import ColorProjectileComponent
from engine.components.avatar_colors import AvatarColors
from games.voxel_world.systems.projectile_system import ProjectileSystem
from panda3d.core import LVector3f

# Mock Base
class MockGame:
    class MockLoader:
        def loadModel(self, path): return None
        
    class MockRender:
        def attachNewNode(self, name): return MockNode()
            
    class MockBase:
        def __init__(self):
            self.loader = MockGame.MockLoader()
            self.render = MockGame.MockRender()

    def __init__(self):
        self.base = self.MockBase()

class MockNode:
    def reparentTo(self, parent): pass
    def setPos(self, pos): pass
    def setScale(self, scale): pass
    def setColor(self, color): pass
    def removeNode(self): pass
    def destroy(self): pass # For PickupVisual wrapper

@pytest.fixture
def proj_world():
    world = World()
    event_bus = EventBus()
    game = MockGame()
    system = ProjectileSystem(world, event_bus, game)
    world.add_system(system)
    return world, system, event_bus

def test_projectile_spawn(proj_world):
    world, system, bus = proj_world
    
    class Event:
        pass
    
    # EventBus.publish passes args as attributes on a dynamic object
    # We simulate this by passing kwargs
    bus.publish("spawn_projectile", 
        position=LVector3f(0, 0, 0),
        velocity=LVector3f(1, 0, 0),
        color_name="red",
        owner_id="p1"
    )
    
    # Check creation
    ents = world.get_entities_with(ColorProjectileComponent)
    assert len(ents) == 1
    
    comp = world.get_component(list(ents)[0], ColorProjectileComponent)
    assert comp.color_name == "red"
    assert comp.velocity == LVector3f(1, 0, 0)

def test_projectile_hit(proj_world):
    world, system, bus = proj_world
    
    # Create target
    target = world.create_entity()
    world.add_component(target, Transform(position=LVector3f(5, 0, 0)))
    world.add_component(target, AvatarColors())
    
    # Create projectile moving towards target slooooowly to avoid tunneling
    # (Physics is step-based, fast objects tunnel if step > size)
    proj = world.create_entity()
    world.add_component(proj, Transform(position=LVector3f(4.5, 0, 0)))
    world.add_component(proj, ColorProjectileComponent(
        velocity=LVector3f(2.0, 0, 0), # 2.0 * 0.1 = 0.2 step. 4.5 -> 4.7. Dist to 5.0 is 0.3. Hit radius 0.7. Hit!
        color_name="blue",
        owner_id="other"
    ))
    
    # Update
    system.update(0.1)
    
    # Should have hit (radius check 0.5 + 0.2 vs dist 0.5) inside
    # 4.5 -> 5.5 in 0.1s. Passes through 5.0.
    # Logic implementation checks new position dist.
    # 4.5 + 1 = 5.5.
    # Dist sq (5.5 - 5.0)^2 = 0.25. (0.7^2 = 0.49). 0.25 < 0.49. Hit!
    
    # Target should be blue
    colors = world.get_component(target, AvatarColors)
    assert colors.temporary_color is not None
    # Check RGBA match for blue?
    # Actually just check temp timer set
    assert colors.temp_timer > 0
    
    # Projectile should be gone
    assert len(world.get_entities_with(ColorProjectileComponent)) == 0
