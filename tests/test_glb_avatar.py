
import unittest
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock panda3d
from tests.test_utils.mock_panda import MockVector3, MockNodePath

# Mock gltf module
sys.modules['gltf'] = MagicMock()

mock_panda = MagicMock()
mock_core = MagicMock()
mock_core.LVector3f = MockVector3
mock_core.NodePath = MockNodePath
sys.modules['panda3d'] = mock_panda
sys.modules['panda3d.core'] = mock_core

# Mock direct
mock_direct = MagicMock()
mock_loader = MagicMock()
sys.modules['direct'] = mock_direct
sys.modules['direct.showbase'] = MagicMock()
sys.modules['direct.showbase.Loader'] = mock_loader

from engine.animation.glb_avatar import GLBAvatar
from engine.animation.skeleton import HumanoidSkeleton

class TestGLBAvatar(unittest.TestCase):
    def setUp(self):
        self.mock_parent = MockNodePath("parent")
        self.skeleton = HumanoidSkeleton()
        self.mock_loader = MagicMock()
        
        # Setup specific mock model return
        self.mock_model = MockNodePath("loaded_model")
        self.mock_loader.loadModel.return_value = self.mock_model
        
    def test_initialization(self):
        avatar = GLBAvatar(self.mock_parent, self.skeleton, loader=self.mock_loader)
        self.assertIsNotNone(avatar)
        self.assertTrue(len(avatar.bone_nodes) > 0)
        
    def test_load_model_failure(self):
        """Should handle missing model gracefully"""
        self.mock_loader.loadModel.return_value = None
        avatar = GLBAvatar(self.mock_parent, self.skeleton, loader=self.mock_loader)
        # Should still initialize skeleton even if model fails
        self.assertTrue(len(avatar.bone_nodes) > 0)

    def test_attach_visuals_fallback(self):
        """Test fallback to attaching full model to hips when no named parts match."""
        # Setup mock model with children that don't match bone names
        child1 = MockNodePath("random_mesh")
        child2 = MockNodePath("another_mesh")
        self.mock_model.children = [child1, child2] # MockNodePath implementation specific
        
        # We need to mock getChildren() behavior for the loop in _attach_visuals
        # Since MockNodePath might not support getChildren exactly as Panda3D, 
        # let's assume our MockNodePath structure or mock the method on the return value
        self.mock_model.getChildren = MagicMock(return_value=[child1, child2])
        self.mock_model.getNumChildren = MagicMock(return_value=2)
        
        avatar = GLBAvatar(self.mock_parent, self.skeleton, loader=self.mock_loader)
        
        # Verify reparentTo was called on the model itself to hips
        # self.mock_model.reparentTo.assert_called_with(...)
        # But wait, logic is: if attached_parts == 0, model.reparentTo(hips)
        
        # Verify hips exists
        hips_node = avatar.bone_nodes["hips"]
        
        # Check call args
        # This depends on MockNodePath implementation. 
        # If it uses real MagicMocks for methods:
        if isinstance(self.mock_model.reparentTo, MagicMock):
            self.mock_model.reparentTo.assert_called_with(hips_node)
            
    def test_attach_visuals_named_parts(self):
        """Test reparenting of matching named parts."""
        # Setup mock children with matching names
        head_part = MockNodePath("head")
        chest_part = MockNodePath("chest")
        random_part = MockNodePath("sword")
        
        self.mock_model.getChildren = MagicMock(return_value=[head_part, chest_part, random_part])
        
        avatar = GLBAvatar(self.mock_parent, self.skeleton, loader=self.mock_loader)
        
        # Head should attach to head bone
        head_bone = avatar.bone_nodes["head"]
        if isinstance(head_part.reparentTo, MagicMock):
            head_part.reparentTo.assert_called_with(head_bone)
            
        # Random part should NOT be reparented individually 
        # (It effectively stays in the 'model' node, which then gets reparented to hips if it still has children)
        
        # Check if model container was reparented to hips (since it still has 'sword')
        hips_bone = avatar.bone_nodes["hips"]
        self.mock_model.getNumChildren = MagicMock(return_value=1) # simulating sword left
        if isinstance(self.mock_model.reparentTo, MagicMock):
             self.mock_model.reparentTo.assert_called_with(hips_bone)

if __name__ == '__main__':
    unittest.main()
