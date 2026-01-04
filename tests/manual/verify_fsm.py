
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from panda3d.core import LVector3f
from engine.animation.sources import ProceduralAnimationSource
from engine.animation.skeleton import Skeleton, Bone
from engine.animation.core import Transform

# Mocks
class MockController:
    pass

class MockBone:
    def __init__(self, name):
        self.name = name
        self.rest_transform = Transform()

class MockSkeleton(Skeleton):
    def __init__(self):
        self.bones = {}
        for name in ['upper_arm_right', 'upper_arm_left', 'thigh_right', 'thigh_left', 'chest']:
            self.bones[name] = MockBone(name)
            
    def get_bone(self, name):
        return self.bones.get(name)

def verify_fsm():
    controller = MockController()
    source = ProceduralAnimationSource(controller)
    skeleton = MockSkeleton()
    
    print("--- Initial State ---")
    print(f"Current Anim: {source._current_anim}") # Should be 'idle'
    assert source._current_anim == 'idle'
    
    print("\n--- Start Walking (Speed 3.0) ---")
    source.set_movement_state(LVector3f(3, 0, 0), True)
    source.update(0.016, skeleton)
    print(f"Current Anim: {source._current_anim}")
    assert source._current_anim == 'walk'
    
    print("\n--- Start Running (Speed 10.0) ---")
    source.set_movement_state(LVector3f(10, 0, 0), True)
    source.update(0.016, skeleton)
    print(f"Current Anim: {source._current_anim}")
    assert source._current_anim == 'run'
    
    print("\n--- Jump (Ungrounded) ---")
    # Simulate jump input handling which usually sets vertical velocity
    source.set_movement_state(LVector3f(10, 0, 5), False)
    # FSM update inside set_movement_state should detect airborne
    source.update(0.016, skeleton) 
    print(f"Current Anim: {source._current_anim}")
    # Note: Transition might be Fall immediately if we didn't explicitly trigger 'jump' request
    # In my FSM implementation logic:
    # if not grounded: if state not in ['Jump', 'Fall']: request('Fall')
    assert source._current_anim in ['fall_loop', 'jump_start']
    
    print("\n--- Land (Grounded) ---")
    source.set_movement_state(LVector3f(0, 0, 0), True)
    source.update(0.016, skeleton)
    print(f"Current Anim: {source._current_anim}")
    assert source._current_anim == 'land'
    
    print("\n--- Return to Idle ---")
    # Land needs to finish or blend out.
    # In update(), if land and not moving, we check if done?
    # Or just let time pass.
    # For test, let's force movement to break out?
    # Or simulate time passing
    for _ in range(20):
        source.update(0.1, skeleton)
        
    # My logic: if anim == 'land' and speed > 0.5: request walk/run.
    # If speed < 0.1 and not moving... currently logic says:
    # if speed < 0.1: if state != 'Idle': request('Idle')
    # So it should go to Idle eventually.
    
    print(f"Current Anim after waiting: {source._current_anim}")
    assert source._current_anim == 'idle'
    
    print("\n[SUCCESS] FSM verification passed!")

if __name__ == "__main__":
    verify_fsm()
