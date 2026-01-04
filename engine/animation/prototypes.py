
"""
Prototype implementation of FSM-based Animation Controllers.
This demonstrates how we can replace ad-hoc conditional logic with 
direct.fsm.FSM for robust state management.
"""

from direct.fsm.FSM import FSM
from panda3d.core import LVector3f
from engine.core.logger import get_logger

logger = get_logger(__name__)

class AnimationFSM(FSM):
    """Base class for Animation State Machines."""
    
    def __init__(self, name, animator):
        FSM.__init__(self, name)
        self.animator = animator
        # Default transitions could be defined here
        pass

class LocomotionFSM(AnimationFSM):
    """FSM for handling movement states (Idle, Walk, Run, Jump, Fall)."""
    
    def __init__(self, animator):
        AnimationFSM.__init__(self, "LocomotionFSM", animator)
        
        # Define default transitions
        self.defaultTransitions = {
            'Idle': ['Walk', 'Run', 'Jump', 'Fall'],
            'Walk': ['Idle', 'Run', 'Jump', 'Fall'],
            'Run': ['Idle', 'Walk', 'Jump', 'Fall'],
            'Jump': ['Fall', 'Land'], # Jump usually transitions to Fall at apex
            'Fall': ['Land', 'Idle', 'Walk', 'Run'], # Land might be skipped if instant
            'Land': ['Idle', 'Walk', 'Run']
        }
        
        self.velocity = LVector3f(0, 0, 0)
        self.is_grounded = True
        
    # ------------------------------------------------------------------
    # State Logic
    # ------------------------------------------------------------------
    
    def enterIdle(self):
        self.animator.play("idle", loop=True, blend_time=0.2)
        
    def enterWalk(self):
        self.animator.play("walk", loop=True, blend_time=0.2)
        
    def enterRun(self):
        self.animator.play("run", loop=True, blend_time=0.2)
        
    def enterJump(self):
        # One-shot animation
        self.animator.play("jump_start", loop=False, blend_time=0.1)
        
    def enterFall(self):
        self.animator.play("fall_loop", loop=True, blend_time=0.3)
        
    def enterLand(self):
        self.animator.play("land", loop=False, blend_time=0.1)
        
    # ------------------------------------------------------------------
    # Update Logic (Called by System)
    # ------------------------------------------------------------------
    
    def update(self, dt, velocity, is_grounded):
        """Analyze physics state and request FSM transitions."""
        self.velocity = velocity
        
        speed = velocity.length()
        
        # Airborne Logic
        if not is_grounded:
            if self.state not in ['Jump', 'Fall']:
                # If we just walked off a ledge
                self.request('Fall')
            elif self.state == 'Jump':
                # Check if we should transition to Fall (e.g. at apex)
                # For this prototype, assume 'jump' anim handles it or we switch manually
                pass
            return
            
        # Grounded Logic
        if self.state in ['Jump', 'Fall']:
            self.request('Land')
            return
            
        if self.state == 'Land':
            # Wait for land anim to finish? 
            # Or just interrupt if moving?
            if speed > 0.1:
                self.request('Walk') # or Run based on speed
            # If land anim finished checking... (requires polling animator)
            # For now, let's just let Land finish or interrupt if moving.
            pass

        # Movement Logic
        if speed < 0.1:
            if self.state != 'Idle':
                self.request('Idle')
        elif speed < 6.0:
            if self.state != 'Walk':
                self.request('Walk')
        else:
            if self.state != 'Run':
                self.request('Run')

# ------------------------------------------------------------------
# Example Usage Mock
# ------------------------------------------------------------------

class MockAnimator:
    def play(self, clip, loop=True, blend_time=0.0):
        print(f"[Animator] Playing '{clip}' (loop={loop}, blend={blend_time})")

if __name__ == "__main__":
    animator = MockAnimator()
    fsm = LocomotionFSM(animator)
    
    print("--- Initial Update (Idle) ---")
    fsm.request('Idle')
    
    print("\n--- Start Walking ---")
    fsm.update(0.016, LVector3f(3, 0, 0), True)
    
    print("\n--- Start Running ---")
    fsm.update(0.016, LVector3f(10, 0, 0), True)
    
    print("\n--- Jump! ---")
    # Usually input triggers Jump request directly, bypassing update() logic for one frame
    fsm.request('Jump')
    
    print("\n--- Mid-Air ---")
    fsm.update(0.016, LVector3f(10, 0, 5), False)
