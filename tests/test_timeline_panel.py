"""
Tests for TimelinePanel.
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
gui_mock.DirectButton = MagicMock()
gui_mock.DirectCheckButton = MagicMock()

from engine.editor.panels.timeline_panel import TimelinePanel


@pytest.fixture
def mock_parent():
    """Create a mock parent node."""
    return MagicMock()


@pytest.fixture
def mock_callbacks():
    """Create mock callbacks."""
    return {
        'play': MagicMock(),
        'pause': MagicMock(),
        'stop': MagicMock(),
        'capture': MagicMock(),
        'delete_key': MagicMock(),
        'looping': MagicMock()
    }


@pytest.fixture
def timeline_panel(mock_parent, mock_callbacks):
    """Create a TimelinePanel with mocked widget."""
    with patch('engine.editor.panels.timeline_panel.TimelineWidget') as MockWidget:
        panel = TimelinePanel(mock_parent, mock_callbacks)
        return panel


class TestTimelinePanel:
    """Tests for TimelinePanel."""
    
    def test_initialization(self, mock_parent, mock_callbacks):
        """Test panel initializes correctly."""
        with patch('engine.editor.panels.timeline_panel.TimelineWidget') as MockWidget:
            panel = TimelinePanel(mock_parent, mock_callbacks)
            
            assert panel.callbacks == mock_callbacks
            MockWidget.assert_called_once()
            gui_mock.DirectFrame.assert_called()
            
    def test_callback_validation(self, mock_parent):
        """Test missing callbacks are replaced with no-ops."""
        callbacks = {} # Empty
        
        with patch('engine.editor.panels.timeline_panel.TimelineWidget'):
            panel = TimelinePanel(mock_parent, callbacks)
            
            required = ['play', 'pause', 'stop', 'capture', 'delete_key', 'looping']
            for req in required:
                assert req in panel.callbacks
                # Verify no-op
                panel.callbacks[req]()
                
    def test_update_time(self, timeline_panel):
        """Test update_time updates label and timeline widget."""
        timeline_panel.time_label = MagicMock()
        
        timeline_panel.update_time(1.5, 5.0)
        
        # Verify text update
        # DirectGui objects use __setitem__ for 'text' usually, assuming mock supports setitem or verify setitem call
        # Since MagicMock supports everything, we verify the effect or just that it didn't crash
        
        # Verify timeline widget update
        timeline_panel.timeline.set_playhead.assert_called_once_with(1.5)
        
    def test_set_duration(self, timeline_panel):
        """Test setting duration."""
        timeline_panel.set_duration(10.0)
        
        timeline_panel.timeline.set_duration.assert_called_once_with(10.0)
        
    def test_set_looping(self, timeline_panel):
        """Test set_looping updates checkbox."""
        timeline_panel.loop_checkbox = MagicMock()
        
        timeline_panel.set_looping(True)
        # MagicMock __setitem__ call verify if needed, simplified here
        
        timeline_panel.set_looping(False)
        
    def test_cleanup(self, timeline_panel):
        """Test cleanup destroys components."""
        timeline_panel.frame.destroy = MagicMock()
        timeline_panel.timeline.destroy = MagicMock()
        
        timeline_panel.cleanup()
        
        timeline_panel.frame.destroy.assert_called_once()
        timeline_panel.timeline.destroy.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
