"""
Test for 3D name tag system.
"""

import unittest
from unittest.mock import MagicMock, patch
from panda3d.core import NodePath, Vec3


class TestNameTag(unittest.TestCase):
    """Test NameTag class."""
    
    @patch('engine.ui.name_tag.TextNode')
    def test_name_tag_creation(self, mock_text_node):
        """Test that name tag can be created."""
        from engine.ui.name_tag import NameTag
        
        # Create mock parent node
        parent = MagicMock(spec=NodePath)
        parent.attachNewNode = MagicMock(return_value=MagicMock(spec=NodePath))
        
        # Create name tag
        tag = NameTag(parent, "TestPlayer")
        
        # Verify TextNode was created
        mock_text_node.assert_called_once_with('name_tag')
        
    @patch('engine.ui.name_tag.TextNode')
    def test_set_name(self, mock_text_node):
        """Test changing player name."""
        from engine.ui.name_tag import NameTag
        
        parent = MagicMock(spec=NodePath)
        parent.attachNewNode = MagicMock(return_value=MagicMock(spec=NodePath))
        
        tag = NameTag(parent, "Player1")
        
        # Change name
        tag.set_name("Player2")
        
        # Verify setText was called
        tag.text_node.setText.assert_called_with("Player2")


if __name__ == '__main__':
    unittest.main()
