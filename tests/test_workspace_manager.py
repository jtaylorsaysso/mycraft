import sys
import pytest
from unittest.mock import MagicMock, Mock, patch

# Mock Panda3D modules before importing workspace
gui_mock = MagicMock()
sys.modules['direct'] = MagicMock()
sys.modules['direct.showbase'] = MagicMock()
sys.modules['direct.showbase.DirectObject'] = MagicMock()
sys.modules['direct.gui'] = MagicMock()
sys.modules['direct.gui.DirectGui'] = gui_mock

# Setup DirectGui components
gui_mock.DirectFrame = MagicMock()
gui_mock.DirectButton = MagicMock()
gui_mock.DirectLabel = MagicMock()
gui_mock.DGG = MagicMock()

from engine.editor.workspace_manager import WorkspaceManager
from engine.editor.workspace import Workspace


class MockWorkspace:
    """Mock workspace for testing."""
    
    def __init__(self, app, name: str):
        self.app = app
        self.name = name
        self.active = False
        self.enter_called = False
        self.exit_called = False
        self.cleanup_called = False
        self.selection = None
        
    def enter(self):
        self.active = True
        self.enter_called = True
        
    def exit(self):
        self.active = False
        self.exit_called = True
        
    def cleanup(self):
        self.cleanup_called = True
        
    def set_selection(self, sel):
        self.selection = sel
        
    def update(self, dt):
        pass


@pytest.fixture
def mock_app():
    """Create a mock EditorApp."""
    app = MagicMock()
    app.aspect2d = MagicMock()
    return app


@pytest.fixture
def workspace_manager(mock_app):
    """Create a WorkspaceManager with mocked UI."""
    return WorkspaceManager(mock_app)


class TestWorkspaceManager:
    """Tests for WorkspaceManager."""
    
    def test_initialization(self, workspace_manager):
        """Test manager initializes with empty state."""
        assert workspace_manager.workspaces == {}
        assert workspace_manager.workspace_order == []
        assert workspace_manager.active_workspace_name is None
        assert workspace_manager.selection is not None
        
    def test_add_workspace(self, workspace_manager, mock_app):
        """Test adding a workspace."""
        ws = MockWorkspace(mock_app, "Test")
        
        workspace_manager.add_workspace("Test", ws)
        
        assert "Test" in workspace_manager.workspaces
        assert workspace_manager.workspaces["Test"] == ws
        assert "Test" in workspace_manager.workspace_order
        
    def test_add_workspace_injects_selection(self, workspace_manager, mock_app):
        """Test that adding a workspace injects shared selection."""
        ws = MockWorkspace(mock_app, "Test")
        
        workspace_manager.add_workspace("Test", ws)
        
        assert ws.selection == workspace_manager.selection
        
    def test_first_workspace_auto_activates(self, workspace_manager, mock_app):
        """Test that first workspace is automatically activated."""
        ws = MockWorkspace(mock_app, "Test")
        
        workspace_manager.add_workspace("Test", ws)
        
        assert workspace_manager.active_workspace_name == "Test"
        assert ws.enter_called
        assert ws.active
        
    def test_second_workspace_does_not_auto_activate(self, workspace_manager, mock_app):
        """Test that second workspace doesn't auto-activate."""
        ws1 = MockWorkspace(mock_app, "First")
        ws2 = MockWorkspace(mock_app, "Second")
        
        workspace_manager.add_workspace("First", ws1)
        workspace_manager.add_workspace("Second", ws2)
        
        assert workspace_manager.active_workspace_name == "First"
        assert ws1.active
        assert not ws2.active
        
    def test_switch_to_valid_workspace(self, workspace_manager, mock_app):
        """Test switching to a valid workspace."""
        ws1 = MockWorkspace(mock_app, "First")
        ws2 = MockWorkspace(mock_app, "Second")
        
        workspace_manager.add_workspace("First", ws1)
        workspace_manager.add_workspace("Second", ws2)
        
        # Reset flags
        ws1.enter_called = False
        ws1.exit_called = False
        
        workspace_manager.switch_to("Second")
        
        assert workspace_manager.active_workspace_name == "Second"
        assert ws1.exit_called
        assert not ws1.active
        assert ws2.enter_called
        assert ws2.active
        
    def test_switch_to_invalid_workspace(self, workspace_manager, mock_app):
        """Test switching to non-existent workspace does nothing."""
        ws = MockWorkspace(mock_app, "Test")
        workspace_manager.add_workspace("Test", ws)
        
        workspace_manager.switch_to("NonExistent")
        
        # Should remain on Test
        assert workspace_manager.active_workspace_name == "Test"
        
    def test_switch_to_same_workspace(self, workspace_manager, mock_app):
        """Test switching to already-active workspace is a no-op."""
        ws = MockWorkspace(mock_app, "Test")
        workspace_manager.add_workspace("Test", ws)
        
        # Reset flags
        ws.enter_called = False
        ws.exit_called = False
        
        workspace_manager.switch_to("Test")
        
        # Should not call enter/exit again
        assert not ws.enter_called
        assert not ws.exit_called
        
    def test_get_workspace_names(self, workspace_manager, mock_app):
        """Test getting list of workspace names."""
        ws1 = MockWorkspace(mock_app, "First")
        ws2 = MockWorkspace(mock_app, "Second")
        ws3 = MockWorkspace(mock_app, "Third")
        
        workspace_manager.add_workspace("First", ws1)
        workspace_manager.add_workspace("Second", ws2)
        workspace_manager.add_workspace("Third", ws3)
        
        names = workspace_manager.get_workspace_names()
        
        assert names == ["First", "Second", "Third"]
        
    def test_get_workspace_names_returns_copy(self, workspace_manager, mock_app):
        """Test that get_workspace_names returns a copy, not reference."""
        ws = MockWorkspace(mock_app, "Test")
        workspace_manager.add_workspace("Test", ws)
        
        names = workspace_manager.get_workspace_names()
        names.append("Hacked")
        
        # Original should be unchanged
        assert workspace_manager.workspace_order == ["Test"]
        
    def test_update_calls_active_workspace(self, workspace_manager, mock_app):
        """Test that update() calls active workspace's update."""
        ws = MockWorkspace(mock_app, "Test")
        ws.update = MagicMock()
        
        workspace_manager.add_workspace("Test", ws)
        workspace_manager.update(0.016)
        
        ws.update.assert_called_once_with(0.016)
        
    def test_update_does_nothing_when_no_active(self, workspace_manager):
        """Test that update() does nothing when no workspace is active."""
        # Should not raise
        workspace_manager.update(0.016)
        
    def test_cleanup_calls_all_workspaces(self, workspace_manager, mock_app):
        """Test that cleanup() calls cleanup on all workspaces."""
        ws1 = MockWorkspace(mock_app, "First")
        ws2 = MockWorkspace(mock_app, "Second")
        
        workspace_manager.add_workspace("First", ws1)
        workspace_manager.add_workspace("Second", ws2)
        
        workspace_manager.cleanup()
        
        assert ws1.cleanup_called
        assert ws2.cleanup_called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
