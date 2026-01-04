"""
Tests for TransformInspectorPanel.
"""

import sys
import pytest
from unittest.mock import MagicMock, Mock, patch

# Mock Panda3D modules
gui_mock = MagicMock()
sys.modules['direct'] = MagicMock()
sys.modules['direct.showbase'] = MagicMock()
sys.modules['direct.gui'] = MagicMock()
sys.modules['direct.gui.DirectGui'] = gui_mock
sys.modules['panda3d.core'] = MagicMock()

# Setup DirectGui components
gui_mock.DirectFrame = MagicMock()
gui_mock.DirectLabel = MagicMock()
gui_mock.DirectSlider = MagicMock()

from engine.editor.panels.transform_inspector import TransformInspectorPanel


@pytest.fixture
def mock_parent():
    """Create a mock parent node."""
    return MagicMock()


@pytest.fixture
def mock_callbacks():
    """Create mock callbacks."""
    return {
        'pos': MagicMock(),
        'rot': MagicMock(),
        'length': MagicMock()
    }


@pytest.fixture
def mock_selection():
    """Create a mock selection."""
    selection = MagicMock()
    selection.bone = None
    return selection


class TestTransformInspectorPanel:
    """Tests for TransformInspectorPanel."""
    
    def test_initialization(self, mock_parent, mock_selection, mock_callbacks):
        """Test panel initializes correctly."""
        panel = TransformInspectorPanel(mock_parent, mock_selection, mock_callbacks)
        
        assert panel.selection == mock_selection
        assert panel.callbacks == mock_callbacks
        
        # Check frame creation
        gui_mock.DirectFrame.assert_called()
        gui_mock.DirectLabel.assert_called()
        gui_mock.DirectSlider.assert_called()
        
    def test_callback_validation(self, mock_parent, mock_selection):
        """Test missing callbacks are replaced with no-ops."""
        # Missing 'length' callback
        incomplete_callbacks = {
            'pos': MagicMock(),
            'rot': MagicMock()
        }
        
        panel = TransformInspectorPanel(mock_parent, mock_selection, incomplete_callbacks)
        
        assert 'length' in panel.callbacks
        assert callable(panel.callbacks['length'])
        
        # Test no-op doesn't crash
        panel.callbacks['length'](1.0)
        
    def test_update_shows_panel_when_bone_selected(self, mock_parent, mock_selection, mock_callbacks):
        """Test update shows panel if bone is selected."""
        panel = TransformInspectorPanel(mock_parent, mock_selection, mock_callbacks)
        
        # Mock bone selection
        mock_selection.bone = "Head"
        
        # Reset frame mock to track calls
        panel.frame.show = MagicMock()
        panel.bone_label = MagicMock() # Mock the label wrapper
        
        panel.update()
        
        panel.frame.show.assert_called_once()
        # Ensure label text is updated (this is harder to test with mocks, assuming DirectLabel wrapper)
        
    def test_update_hides_panel_when_no_selection(self, mock_parent, mock_selection, mock_callbacks):
        """Test update hides panel if no bone selected."""
        panel = TransformInspectorPanel(mock_parent, mock_selection, mock_callbacks)
        
        mock_selection.bone = None
        panel.frame.hide = MagicMock()
        
        panel.update()
        
        panel.frame.hide.assert_called_once()
        
    def test_cleanup(self, mock_parent, mock_selection, mock_callbacks):
        """Test cleanup destroys frame."""
        panel = TransformInspectorPanel(mock_parent, mock_selection, mock_callbacks)
        panel.frame.destroy = MagicMock()
        
        panel.cleanup()
        
        panel.frame.destroy.assert_called_once()
        
    def test_sliders_created(self, mock_parent, mock_selection, mock_callbacks):
        """Test that sliders are created and stored."""
        panel = TransformInspectorPanel(mock_parent, mock_selection, mock_callbacks)
        
        expected_sliders = [
            'Position_x', 'Position_y', 'Position_z',
            'Rotation_h', 'Rotation_p', 'Rotation_r'
        ]
        
        for name in expected_sliders:
            assert name in panel.sliders


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
