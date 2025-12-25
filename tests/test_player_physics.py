
import sys
from unittest.mock import MagicMock

# Mock panda3d before importing anything else
mock_panda = MagicMock()
mock_core = MagicMock()

# Setup LVector3f mock that behaves somewhat like a vector
class MockVector3:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
        
    def __repr__(self):
        return f"Vec3({self.x}, {self.y}, {self.z})"
    
    def __add__(self, other):
        return MockVector3(self.x + other.x, self.y + other.y, self.z + other.z)
        
    def __sub__(self, other):
        return MockVector3(self.x - other.x, self.y - other.y, self.z - other.z)
        
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return MockVector3(self.x * other, self.y * other, self.z * other)
        return MockVector3(self.x * other.x, self.y * other.y, self.z * other.z)
        
    def length(self):
        return (self.x**2 + self.y**2 + self.z**2)**0.5
        
    def normalize(self):
        l = self.length()
        if l > 0:
            self.x /= l
            self.y /= l
            self.z /= l

mock_core.LVector3f = MockVector3
mock_core.WindowProperties = MagicMock()
mock_core.ModifierButtons = MagicMock()
mock_core.CollisionHandlerQueue.return_value.getNumEntries.return_value = 0
mock_core.BitMask32.bit.return_value = 1
mock_core.BitMask32.allOff.return_value = 0
mock_panda.core = mock_core
sys.modules['panda3d'] = mock_panda
sys.modules['panda3d.core'] = mock_core

import unittest
from unittest.mock import patch
from engine.systems.input import PlayerControlSystem
from engine.physics import KinematicState

class TestPlayerPhysics(unittest.TestCase):
    def setUp(self):
        self.mock_world = MagicMock()
        self.mock_event_bus = MagicMock()
        self.mock_base = MagicMock()
        self.mock_base.cam.getH.return_value = 0.0 # Facing North
        
        # Mock InputManager
        self.patcher = patch('engine.systems.input.InputManager')
        self.MockInput = self.patcher.start()
        self.mock_input = self.MockInput.return_value
        self.mock_input.mouse_delta = (0, 0)
        self.mock_input.is_key_down.return_value = False
        
        self.system = PlayerControlSystem(self.mock_world, self.mock_event_bus, self.mock_base)
        self.system.initialize()
        
        # Setup mock player
        self.player_id = 1
        self.mock_world.get_entity_by_tag.return_value = self.player_id
        
        self.mock_transform = MagicMock()
        # Use our mock vector
        # Panda3D is Z-up. Position should be (0, 0, 10) to be in air (10 units high).
        self.mock_transform.position = MockVector3(0, 0, 10)
        
        # Mock Health component with proper attributes
        self.mock_health = MagicMock()
        self.mock_health.invulnerable = False
        self.mock_health.invuln_timer = 0.0
        
        # Setup get_component to return appropriate mocks
        def get_component_side_effect(entity_id, component_type):
            if component_type.__name__ == 'Transform':
                return self.mock_transform
            elif component_type.__name__ == 'Health':
                return self.mock_health
            return None
        
        self.mock_world.get_component.side_effect = get_component_side_effect
        
        # Manually trigger on_ready since we're not using real World
        # In real usage, World would call this when player entity is created
        self.system.ready = True

    def tearDown(self):
        self.patcher.stop()

    def test_gravity_in_air(self):
        """Verify gravity accelerates player downwards when in air."""
        # Setup: No water system, no ground
        self.system._get_system = MagicMock(return_value=None)
        
        # Run update
        dt = 0.1
        self.system.update(dt)
        
        # Check physics state
        state = self.system.physics_states[self.player_id]
        
        # Should have negative vertical velocity (accelerating down)
        self.assertLess(state.velocity_y, -1.0) # Gravity -20, so -2.0 velocity after 0.1s
        
        # Should have moved down in Z axis (Panda Up)
        # 10.0 + (-2.0 * 0.1) = 9.8 roughly?
        # Integrate logic: entity.y += velocity_y * dt.
        # wrapper.y maps to transform.z.
        self.assertLess(self.mock_transform.position.z, 10.0)

    def test_water_buoyancy(self):
        """Verify reduced gravity/falling speed in water."""
        # Setup: Water system present and player is submerged
        mock_water = MagicMock()
        mock_water.__class__.__name__ = "WaterPhysicsSystem"
        mock_water.is_position_in_water.return_value = True
        mock_water.get_submersion_level.return_value = 1.0
        
        def get_system_side_effect(name):
            if name == "WaterPhysicsSystem": return mock_water
            return None
            
        self.system._get_system = MagicMock(side_effect=get_system_side_effect)
        
        # Initial state falling
        state = self.system.physics_states.setdefault(self.player_id, KinematicState())
        
        # Run update with WATER_GRAVITY (-2.0) vs Normal (-20.0)
        dt = 0.1
        self.system.update(dt)
        
        water_vel = state.velocity_y
        
        # Now reset and check AIR gravity
        mock_water.is_position_in_water.return_value = False
        self.system.physics_states[self.player_id] = KinematicState()
        self.system.update(dt)
        air_vel = self.system.physics_states[self.player_id].velocity_y
        
        # Water velocity should be much higher (closer to 0) than air velocity (very negative)
        # Water: -0.2
        # Air: -2.0
        self.assertGreater(water_vel, air_vel)
        self.assertAlmostEqual(water_vel, -0.2, delta=0.1)

    def test_water_drag(self):
        """Verify drag slows down movement in water."""
        # Setup: Water system
        mock_water = MagicMock()
        mock_water.__class__.__name__ = "WaterPhysicsSystem"
        mock_water.is_position_in_water.return_value = True
        
        def get_system_side_effect(name):
             if name == "WaterPhysicsSystem": return mock_water
             return None
        self.system._get_system = MagicMock(side_effect=get_system_side_effect)
        
        # Moving fast state
        state = self.system.physics_states.setdefault(self.player_id, KinematicState())
        state.velocity_x = 20.0
        
        # Run update
        dt = 0.1
        self.system.update(dt)
        
        # Should slow down significantly due to drag
        self.assertLess(state.velocity_x, 20.0)
        
        # Check specific drag logic: vel += (target - vel) * drag
        # target=0, vel=20, drag=2.0 * 0.1 = 0.2
        # new_vel = 20 + (0 - 20) * 0.2 = 20 - 4 = 16
        self.assertAlmostEqual(state.velocity_x, 16.0, delta=1.0)

if __name__ == '__main__':
    unittest.main()
