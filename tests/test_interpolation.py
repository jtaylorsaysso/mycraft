import unittest
from unittest.mock import MagicMock
import sys
import os
import math

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ----------------- MOCKS -----------------

class FakeVec3:
    def __init__(self, x=0, y=0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        
    def __add__(self, other):
        return FakeVec3(self.x + other.x, self.y + other.y, self.z + other.z)
        
    def __sub__(self, other):
        return FakeVec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return FakeVec3(self.x * other, self.y * other, self.z * other)
        return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return FakeVec3(self.x / other, self.y / other, self.z / other)
        return NotImplemented

    def length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
        
    def __eq__(self, other):
        if not isinstance(other, FakeVec3):
            return False
        return abs(self.x - other.x) < 0.001 and abs(self.y - other.y) < 0.001 and abs(self.z - other.z) < 0.001

    def __repr__(self):
        return f"Vec3({self.x}, {self.y}, {self.z})"

class FakeEntity:
    def __init__(self, **kwargs):
        self.position = kwargs.get('position', FakeVec3(0,0,0))
        if isinstance(self.position, tuple):
             self.position = FakeVec3(*self.position)
             
        self.rotation_y = kwargs.get('rotation_y', 0.0)
        self.parent = kwargs.get('parent', None)
        self.model = kwargs.get('model', None)
        self.color = kwargs.get('color', None)
        self.scale = kwargs.get('scale', 1.0)
        self.children = []
        if self.parent:
            self.parent.children.append(self)

# Mock ursina module structure - but don't pollute sys.modules at module level
mock_ursina = MagicMock()
mock_ursina.Entity = FakeEntity
mock_ursina.Vec3 = FakeVec3
mock_ursina.color = MagicMock()
mock_ursina.color.azure = "azure"
mock_ursina.color.rgb = lambda r,g,b: (r,g,b)

# Mock time
mock_time = MagicMock()
mock_time.dt = 0.016
mock_ursina.time = mock_time

# Mock lerp
def fake_lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    if isinstance(a, FakeVec3):
        return a + (b - a) * t
    return a + (b - a) * t
mock_ursina.lerp = fake_lerp

# Only mock ursina for this module's imports
# Store original state
_original_ursina = sys.modules.get('ursina')
sys.modules['ursina'] = mock_ursina


# ----------------- TEST -----------------

from games.voxel_world.entities.remote_player import RemotePlayer

class TestInterpolation(unittest.TestCase):
    def setUp(self):
        # Reset time dt default
        sys.modules['ursina'].time.dt = 0.016
        
        self.player = RemotePlayer()
        # Reset position manually to ensure clean state
        self.player.position = FakeVec3(0, 0, 0)
        self.player.rotation_y = 0
        self.player.target_position = FakeVec3(0, 0, 0)
        self.player.target_rotation = 0
        
    def test_initialization(self):
        self.assertEqual(self.player.lerp_speed, 10.0)
        # Check that mannequin was created (AnimatedMannequin as child)
        self.assertTrue(hasattr(self.player, 'mannequin'))
        self.assertTrue(hasattr(self.player, 'animation_controller'))
        
    def test_interpolation_movement(self):
        target = FakeVec3(2, 0, 0)
        self.player.set_target([2, 0, 0], 0)
        
        # Initial pos should be 0
        self.assertEqual(self.player.position.x, 0)
        
        # Update 1
        self.player.update()
        # 0 + (2-0)*0.16 = 0.32
        self.assertAlmostEqual(self.player.position.x, 0.32, places=3)
        
        # Update 2
        self.player.update()
        # 0.32 + (2-0.32)*0.16 = 0.32 + 0.2688 = 0.5888
        self.assertAlmostEqual(self.player.position.x, 0.589, places=2)

    def test_teleport_on_large_distance(self):
        self.player.position = FakeVec3(0, 0, 0)
        
        # Set target 10 units away
        self.player.set_target([10, 0, 0], 0)
        
        # Should teleport immediately
        self.assertEqual(self.player.position.x, 10)

    def test_rotation_interpolation(self):
        self.player.rotation_y = 0
        self.player.set_target([0, 0, 0], 90)
        
        self.player.update()
        # 0 + (90-0)*0.16 = 14.4
        self.assertAlmostEqual(self.player.rotation_y, 14.4, places=1)

def teardown_module():
    """Restore original ursina module state after all tests."""
    if _original_ursina is None:
        sys.modules.pop('ursina', None)
    else:
        sys.modules['ursina'] = _original_ursina

if __name__ == '__main__':
    unittest.main()
