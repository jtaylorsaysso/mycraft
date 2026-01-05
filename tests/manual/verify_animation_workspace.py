
import sys
import unittest
from unittest.mock import MagicMock

# Mock Panda3D
sys.modules['panda3d.core'] = MagicMock()
from panda3d.core import NodePath, ClockObject

# Mock DirectGui
sys.modules['direct.gui.DirectGui'] = MagicMock()
sys.modules['direct.showbase.DirectObject'] = MagicMock()
sys.modules['engine.editor.app'] = MagicMock()
sys.modules['direct.task.Task'] = MagicMock()
sys.modules['direct.interval.IntervalGlobal'] = MagicMock()

# Mock Animation Core (partial)
# We need real VoxelAnimator logic, so we let it import real core if possible?
# But core imports panda3d.
# Let's mock panda3d components but allow core to function if possible.
# Actually, VoxelAnimator needs real logic.
# Core imports: NodePath, LVector3f, LQuaternionf, LMatrix4f
# If we mock these, math might fail.
# So we should probably rely on the fact that VoxelAnimator uses them for calc.

# Let's just mock the Workspace environment but import the real Workspace class.

class TestAnimationWorkspaceLogic(unittest.TestCase):
    def setUp(self):
        # Setup mocks
        self.mock_app = MagicMock()
        self.mock_app.asset_manager = MagicMock()
        self.mock_app.anim_registry = MagicMock()
        self.mock_app.render = MagicMock()
        self.mock_app.aspect2d = MagicMock()
        self.mock_app.taskMgr = MagicMock()
        self.mock_app.camera = MagicMock()
        
        # Mock global clock
        self.mock_clock = MagicMock()
        self.mock_clock.getDt.return_value = 0.016
        ClockObject.getGlobalClock = MagicMock(return_value=self.mock_clock)
        
        # Import Workspace (delayed to allow mocks)
        from engine.editor.workspaces.animation_workspace import AnimationWorkspace
        from engine.animation.core import AnimationClip, Keyframe, AnimationEvent
        
        self.AnimationWorkspace = AnimationWorkspace
        self.AnimationClip = AnimationClip
        self.AnimationEvent = AnimationEvent

    def test_initialization(self):
        ws = self.AnimationWorkspace(self.mock_app)
        self.assertIsNotNone(ws.animator)
        self.assertIsNotNone(ws.preview_rig)

    def test_play_logic(self):
        ws = self.AnimationWorkspace(self.mock_app)
        
        # Setup mock clip
        clip = self.AnimationClip("test_clip", duration=1.0, keyframes=[])
        ws.current_clip = clip
        ws.current_clip_name = "test_clip"
        
        # Verify initial state
        self.assertFalse(ws.playing)
        
        # Call Play
        ws._on_play()
        
        self.assertTrue(ws.playing)
        self.assertTrue(ws.animator.playing)
        self.mock_app.taskMgr.add.assert_called_with(ws._update_playback, "AnimWSUpdate")
        
        # Verify Update
        task = MagicMock()
        ws._update_playback(task)
        
        # Animator should have updated
        # We can't easily assert animator.update called because it's a real object?
        # Or did we mock VoxelAnimator? No, we imported real one.
        # But VoxelAnimator relies on VoxelRig which relies on Panda3D NodePath.
        # Since NodePath is mocked, apply_pose might fail if it tries to call real methods?
        # Transform.apply_to_node calls node.setPos, node.setHpr, node.setScale.
        # Ensure our Mock NodePath supports these.
        
        # Since NodePath is MagicMock, they should absorb calls.
        
    def test_event_logging(self):
        ws = self.AnimationWorkspace(self.mock_app)
        
        # Setup event logic
        ws._log_event("test_event", {"some": "data"})
        
        # Verify UI was updated - mock label
        # ws.event_log_label is a MagicMock
        # It's referenced via dictionary access ['text'] = ...
        # MagicMock supports __setitem__.
        
        # Check that show() was called
        ws.event_log_label.show.assert_called()

if __name__ == '__main__':
    unittest.main()
