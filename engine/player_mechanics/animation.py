"""Animation mechanic for player mannequin."""

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from panda3d.core import LVector3f

class AnimationMechanic(PlayerMechanic):
    """Handles player mannequin rendering and animation."""
    
    priority = 5  # Run last (after movement and camera)
    exclusive = False
    
    def __init__(self, base):
        self.base = base
        self.local_mannequin = None
        self.local_animation_controller = None
    
    def initialize(self, player_id, world):
        """Called when player is ready."""
        try:
            from engine.animation.mannequin import AnimatedMannequin, AnimationController
            
            # Create the mannequin (visuals)
            # We attach to render instead of player transform because we want to 
            # control rotation independent of the physics capsule (which doesn't rotate with camera)
            self.local_mannequin = AnimatedMannequin(
                self.base.render, 
                body_color=(0.2, 0.8, 0.2, 1.0) # Greenish for local player
            )
            
            # Create animation controller
            self.local_animation_controller = AnimationController(self.local_mannequin)
            print("✅ AnimationMechanic: Mannequin created successfully")
            
        except ImportError as e:
            print(f"❌ AnimationMechanic: Animation system error: {e}")
            self.local_mannequin = None
        except Exception as e:
            print(f"❌ AnimationMechanic: Unexpected error creating mannequin: {e}")
            self.local_mannequin = None
            
    def update(self, ctx: PlayerContext) -> None:
        if not self.local_mannequin:
            return
            
        # 1. Handle Visibility based on Camera Mode
        if ctx.camera_mode == 'first_person':
            if self.local_mannequin.root.isHidden() == False:
                print(f"👻 Hiding mannequin (first-person mode)")
            self.local_mannequin.root.hide()
            return  # No need to update animations if invisible
        else:
            if self.local_mannequin.root.isHidden():
                print(f"👁️ Showing mannequin (third-person mode)")
            self.local_mannequin.root.show()
            
        # 2. Sync Position
        # Match mannequin position to physics entity position
        # Physics position is at the feet/bottom of capsule usually
        self.local_mannequin.root.setPos(ctx.transform.position)
        
        # 3. Sync Rotation
        # In third person, character should face camera direction (yaw)
        # We get this from the camera itself since it's the source of truth for view dir
        cam_yaw = self.base.cam.getH()
        self.local_mannequin.root.setH(cam_yaw)
        
        # 4. Update Animations
        if self.local_animation_controller:
            # Velocity needed for animation blending (idle vs run)
            # ctx.state velocity is in world units/sec
            velocity = LVector3f(
                ctx.state.velocity_x, 
                ctx.state.velocity_y, 
                ctx.state.velocity_z
            )
            
            self.local_animation_controller.update(
                ctx.dt, 
                velocity, 
                ctx.state.grounded
            )
            
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.local_mannequin:
            self.local_mannequin.cleanup()
            self.local_mannequin = None
            self.local_animation_controller = None
