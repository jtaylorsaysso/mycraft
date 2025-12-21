import pytest
import sys
from unittest.mock import MagicMock

# --- Global Panda3D Mocks ---
# These are required because many engine modules import panda3d/direct at module level,
# and we want to allow test collection even if Panda3D is not installed in the environment.

if 'panda3d' not in sys.modules:
    mock_panda = MagicMock()
    mock_core = MagicMock()
    
    # Simple MockVector3 that behaves like LVector3f
    class MockVector3:
        def __init__(self, x=0, y=0, z=0):
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)
        def __add__(self, other): return MockVector3(self.x + other.x, self.y + other.y, self.z + other.z)
        def __sub__(self, other): return MockVector3(self.x - other.x, self.y - other.y, self.z - other.z)
        def __mul__(self, other):
            if isinstance(other, (int, float)): return MockVector3(self.x * other, self.y * other, self.z * other)
            return MockVector3(self.x * other.x, self.y * other.y, self.z * other.z)
        def length(self):
            import math
            return math.sqrt(self.x**2 + self.y**2 + self.z**2)
        def __repr__(self): return f"Vec3({self.x}, {self.y}, {self.z})"

    # Simple MockVector2 that behaves like LVector2f
    class MockVector2:
        def __init__(self, x=0, y=0):
            self.x = float(x)
            self.y = float(y)
        def __add__(self, other): return MockVector2(self.x + other.x, self.y + other.y)
        def __sub__(self, other): return MockVector2(self.x - other.x, self.y - other.y)
        def __mul__(self, other):
            if isinstance(other, (int, float)): return MockVector2(self.x * other, self.y * other)
            return MockVector2(self.x * other.x, self.y * other.y)
        def __repr__(self): return f"Vec2({self.x}, {self.y})"

    mock_core.LVector3f = MockVector3
    mock_core.LVector2f = MockVector2
    mock_core.NodePath = MagicMock
    mock_core.WindowProperties = MagicMock
    mock_core.ModifierButtons = MagicMock
    mock_panda.core = mock_core
    sys.modules['panda3d'] = mock_panda
    sys.modules['panda3d.core'] = mock_core


if 'direct' not in sys.modules:
    mock_direct = MagicMock()
    sys.modules['direct'] = mock_direct
    sys.modules['direct.showbase'] = MagicMock()
    sys.modules['direct.showbase.ShowBase'] = MagicMock()
    sys.modules['direct.interval'] = MagicMock()
    sys.modules['direct.interval.IntervalGlobal'] = MagicMock()
    sys.modules['direct.gui'] = MagicMock()
    sys.modules['direct.gui.DirectGui'] = MagicMock()
    sys.modules['direct.task'] = MagicMock()
    sys.modules['direct.task.TaskManagerGlobal'] = MagicMock()



# Module-level cleanup - runs after an entire test module finishes
_module_cleanup_callbacks = []


@pytest.fixture(scope="module", autouse=True)
def cleanup_module_mocks():
    """Clean up module-level mocks after each test module completes."""
    yield
    
    # After entire module cleanup
    pass
