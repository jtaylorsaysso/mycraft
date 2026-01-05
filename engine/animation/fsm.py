
"""
Animation State Machines.
This module defines Finite State Machines (FSMs) for controlling character animations.
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

class LocomotionFSM(AnimationFSM):
    """FSM for handling movement states (Idle, Walk, Run, Jump, Fall)."""
    
    def __init__(self, animator):
        AnimationFSM.__init__(self, "LocomotionFSM", animator)
        
        # Default transitions
        self.defaultTransitions = {
            'Idle': ['Walk', 'Run', 'Jump', 'Fall'],
            'Walk': ['Idle', 'Run', 'Jump', 'Fall'],
            'Run': ['Idle', 'Walk', 'Jump', 'Fall'],
            'Jump': ['Fall', 'Land', 'Idle', 'Run', 'Walk'], # Jump -> Fall naturally
            'Fall': ['Land', 'Idle', 'Walk', 'Run'],
            'Land': ['Idle', 'Walk', 'Run', 'Jump', 'Fall']
        }
        
        self.velocity = LVector3f(0, 0, 0)
        self.is_grounded = True
        self.speed = 0.0
        
    # ------------------------------------------------------------------
    # State Logic
    # ------------------------------------------------------------------
    
    def enterIdle(self):
        # logger.info("Enter Idle")
        self.animator.play("idle", loop=True, blend_time=0.2)
        
    def enterWalk(self):
        # logger.info("Enter Walk")
        self.animator.play("walk", loop=True, blend_time=0.2)
        
    def enterRun(self):
        # logger.info("Enter Run")
        self.animator.play("run", loop=True, blend_time=0.2)
        
    def enterJump(self):
        # logger.info("Enter Jump")
        self.animator.play("jump_start", loop=False, blend_time=0.1)
        
    def enterFall(self):
        # logger.info("Enter Fall")
        self.animator.play("fall_loop", loop=True, blend_time=0.3)
        
    def enterLand(self):
        # logger.info("Enter Land")
        self.animator.play("land", loop=False, blend_time=0.1)
        
    # ------------------------------------------------------------------
    # Update Logic
    # ------------------------------------------------------------------
    
    def update(self, dt, velocity, is_grounded):
        """Analyze physics state and request FSM transitions.
        
        Args:
            dt: Delta time
            velocity: Current velocity vector
            is_grounded: Boolean indicating if character is on ground
        """
        self.velocity = velocity
        self.speed = velocity.length()
        self.is_grounded = is_grounded
        
        # Airborne Logic
        if not self.is_grounded:
            if self.state not in ['Jump', 'Fall']:
                # If we just walked off a ledge, or if we were Idling
                self.request('Fall')
                
            elif self.state == 'Jump':
                # Check directly if jump animation finished?
                # Or use vertical velocity? 
                # If falling downwards, switch to Fall loop
                if self.velocity.z < -0.1:
                     self.request('Fall')
            return
            
        # Grounded Logic
        if self.state in ['Jump', 'Fall']:
            # Just hit the ground
            self.request('Land')
            return
            
        if self.state == 'Land':
            # If moving significantly, break out of landing
            if self.speed > 0.5:
                if self.speed > 6.0:
                    self.request('Run')
                else:
                    self.request('Walk')
                return
            
            # If standard land anim is done (how to check?), go to Idle.
            # VoxelAnimator doesn't expose 'is_playing(clip)' easily yet.
            # We can check animator.current_clip and animator.playing.
            if self.animator.current_clip == "land" and not self.animator.playing:
                self.request('Idle')
            return

        # Movement Logic (Idle/Walk/Run)
        if self.speed < 0.1:
            if self.state != 'Idle':
                self.request('Idle')
        elif self.speed < 6.0:
            if self.state != 'Walk':
                self.request('Walk')
        else:
            if self.state != 'Run':
                self.request('Run')
