
import pytest
from engine.ecs.world import World
from engine.ecs.events import EventBus
from engine.components.core import Transform, Health
from engine.components.enemy import EnemyComponent
from engine.physics import KinematicState
from games.voxel_world.systems.enemy_system import EnemySystem
from panda3d.core import LVector3f

# Mock Game/Base
class MockGame:
    class MockBase:
        class MockRender:
            def attachNewNode(self, name):
                return MockNode(name)
        render = MockRender()
    base = MockBase()

class MockNode:
    def __init__(self, name):
        self.name = name
    def setPos(self, pos): pass
    def lookAt(self, pos): pass
    def destroy(self): pass
    def removeNode(self): pass
    def attachNewNode(self, name): return MockNode(name)
    def setScale(self, s): pass
    def setColor(self, c): pass
    def setColor(self, c): pass
    def setHpr(self, *args): pass
    def setTwoSided(self, v): pass
    def setColorScale(self, *args): pass

@pytest.fixture
def enemy_world():
    world = World()
    event_bus = EventBus()
    game = MockGame()
    system = EnemySystem(world, event_bus, game)
    world.add_system(system)
    return world, system

def test_enemy_initialization(enemy_world):
    world, system = enemy_world
    
    # Create enemy
    e = world.create_entity()
    world.add_component(e, Transform(position=LVector3f(10, 0, 10)))
    world.add_component(e, Health(current=100, max_hp=100))
    world.add_component(e, EnemyComponent(enemy_type="skeleton", tint_color="red"))
    
    # Update system -> should create visual
    system.update(0.1)
    
    assert e in system.visuals
    assert system.visuals[e].enemy_type == "skeleton"

def test_ai_state_machine(enemy_world):
    world, system = enemy_world
    
    # Create Player
    player = world.create_entity()
    world.register_tag(player, "player")
    world.add_component(player, Transform(position=LVector3f(0, 0, 0)))
    
    # Create Enemy (at 20 units - outside aggro)
    enemy = world.create_entity()
    world.add_component(enemy, Transform(position=LVector3f(20, 0, 0)))
    world.add_component(enemy, Health(current=100, max_hp=100))
    world.add_component(enemy, EnemyComponent(aggro_range=10.0))
    world.add_component(enemy, KinematicState()) # Needed for movement logic
    
    # 1. Update - should be Idle
    system.update(0.1)
    comp = world.get_component(enemy, EnemyComponent)
    assert comp.ai_state == "idle"
    
    # 2. Move Player closer (8 units - inside aggro)
    world.get_component(player, Transform).position = LVector3f(12, 0, 0) # enemy at 20, dist 8
    system.update(0.1)
    assert comp.ai_state == "aggro"
    
    # 3. Check movement request (velocity set on KinematicState)
    kin = world.get_component(enemy, KinematicState)
    # Enemy at 20, player at 12 -> direction -1, 0, 0
    # Velocity x should be negative
    assert kin.velocity_x < 0
    
    # 4. Move Player very close (1 unit - inside attack range 2.0)
    world.get_component(player, Transform).position = LVector3f(19, 0, 0)
    system.update(0.1)
    assert comp.ai_state == "windup"
    assert comp.state_timer > 0
    
    # 5. Wait for windup
    timer = comp.state_timer + 0.1
    system.update(timer)
    assert comp.ai_state == "attack" # Or recovery depending on logic flow in one frame
