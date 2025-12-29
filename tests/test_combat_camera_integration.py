import unittest
from unittest.mock import MagicMock
from panda3d.core import LVector3f
from engine.rendering.combat_camera import CombatCamera
from engine.player_mechanics.targeting_mechanic import TargetingMechanic
from engine.components.camera_state import CameraState, CameraMode
from engine.components.core import Transform, Health
from engine.rendering.base_camera import CameraUpdateContext
from engine.player_mechanics.context import PlayerContext
from engine.input.keybindings import InputAction

class TestCombatCameraIntegration(unittest.TestCase):
    def test_combat_camera_framing(self):
        # Setup
        mock_node = MagicMock()
        mock_node.getPos.return_value = LVector3f(0, -10, 0)
        mock_world = MagicMock()
        
        # Target transform (at 10, 10, 0)
        target_transform = Transform(position=LVector3f(10, 10, 0))
        
        # Mocking get_component for the target entity
        def get_component_side_effect(entity_id, component_type):
            if entity_id == "target_1" and component_type == Transform:
                return target_transform
            return None
            
        mock_world.get_component.side_effect = get_component_side_effect
        
        cam = CombatCamera(mock_node)
        camera_state = CameraState(
            mode=CameraMode.COMBAT,
            yaw=0.0,
            target_entity="target_1"
        )
        
        ctx = CameraUpdateContext(
            camera_node=mock_node,
            camera_state=camera_state,
            target_position=LVector3f(0, 0, 0), # Player at origin
            player_velocity=LVector3f(0, 0, 0),
            mouse_delta=(0, 0),
            dt=0.1,
            world=mock_world
        )
        
        # Update
        cam.update(ctx)
        
        # Verify yaw updated to face target
        # Target is at (10, 10). Player at (0, 0). Vector is (10, 10).
        # atan2(-10, 10) = -45 degrees.
        # Yaw should move from 0 towards -45.
        self.assertLess(camera_state.yaw, 0.0)
        # Pitch should adjust downward (negative) because target is same height but camera is higher?
        # Actually combat camera doesn't enforce height difference in the test, 
        # but logic is pitch += (target_pitch - current) * lerp
        # target_pitch = -10 - (5/dist). Dist ~14.
        self.assertLess(camera_state.pitch, 0.0)
        
    def test_targeting_mechanic_lifecycle(self):
        mechanic = TargetingMechanic()
        
        # Mock World and Entities
        mock_world = MagicMock()
        mock_world.get_entities_with.return_value = {"target_1"}
        
        # Camera forwards
        mock_cam = MagicMock()
        mock_cam.getQuat.return_value.getForward.return_value = LVector3f(0, 1, 0) # Facing North
        mock_world.base.cam = mock_cam
        
        # Camera State for Player
        camera_state = CameraState(mode=CameraMode.EXPLORATION)
        
        # Target Transform
        target_transform = Transform(position=LVector3f(0, 5, 0)) # 5 units north (perfectly aligned)
        
        def get_component_side_effect(eid, type_):
            if eid == "player_1" and type_ == CameraState:
                return camera_state
            if eid == "target_1" and type_ == Transform:
                return target_transform
            if eid == "target_1" and type_ == Health:
                return Health()
            return None
            
        mock_world.get_component.side_effect = get_component_side_effect
        
        # Player Context
        ctx = PlayerContext(
            world=mock_world,
            player_id="player_1",
            transform=Transform(position=LVector3f(0, 0, 0)),
            state=MagicMock(),
            dt=0.016
        )
        ctx.input = MagicMock()
        
        # 1. Pressed Lock-On -> Lock
        ctx.input.is_action_active.return_value = True 
        mechanic.update(ctx)
        
        self.assertEqual(camera_state.mode, CameraMode.COMBAT)
        self.assertEqual(camera_state.target_entity, "target_1")
        
        # 2. Reset cooldown, Pressed Lock-On -> Unlock
        mechanic.lock_cooldown = 0
        mechanic.update(ctx)
        
        self.assertEqual(camera_state.mode, CameraMode.EXPLORATION)
        self.assertIsNone(camera_state.target_entity)
        
if __name__ == '__main__':
    unittest.main()
