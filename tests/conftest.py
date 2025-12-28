import pytest
import sys
from unittest.mock import MagicMock

# --- Global Panda3D Mocks ---
# These are required because many engine modules import panda3d/direct at module level,
# and we want to allow test collection even if Panda3D is not installed in the environment.

if 'panda3d' not in sys.modules:
    from tests.test_utils.mock_panda import (
        MockVector3, MockVector2, MockNodePath,
        MockCollisionHandlerQueue, MockCollisionTraverser
    )
    mock_panda = MagicMock()
    mock_core = MagicMock()
    
    mock_core.LVector3f = MockVector3
    mock_core.LVector2f = MockVector2
    mock_core.NodePath = MockNodePath
    mock_core.CollisionHandlerQueue = MockCollisionHandlerQueue
    mock_core.CollisionTraverser = MockCollisionTraverser
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
