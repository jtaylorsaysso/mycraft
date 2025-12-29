from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.input.keybindings import InputAction
from engine.components.camera_state import CameraState, CameraMode
from engine.components.core import Transform, Health
from panda3d.core import LVector3f
import math

class TargetingMechanic(PlayerMechanic):
    """Handles target selection and locking logic."""
    
    priority = 52  # Run before movement/camera, after input
    exclusive = False
    
    def __init__(self):
        self.lock_cooldown = 0.0
        self.max_lock_distance = 25.0  # Range in units
    
    def update(self, ctx: PlayerContext) -> None:
        self.lock_cooldown = max(0, self.lock_cooldown - ctx.dt)
        
        # Check for Lock-On toggle
        if ctx.input.is_action_active(InputAction.LOCK_ON) and self.lock_cooldown <= 0:
            self.lock_cooldown = 0.3  # Debounce
            self._toggle_lock(ctx)
            
        # Verify current target is still valid
        self._validate_lock(ctx)
            
    def _toggle_lock(self, ctx: PlayerContext):
        cam_state = ctx.world.get_component(ctx.player_id, CameraState)
        if not cam_state:
            return
            
        # Check if already locked
        if cam_state.mode == CameraMode.COMBAT and cam_state.target_entity:
            # Unlock
            self._unlock(cam_state)
            print("🔓 Target unlocked")
        else:
            # Try to lock
            target = self._find_best_target(ctx)
            if target:
                cam_state.mode = CameraMode.COMBAT
                cam_state.target_entity = target
                print(f"🔒 Locked on target: {target}")
            else:
                # Could play a "fail" sound or feedback
                print("❌ No valid targets in range")
                # Optional: Reset camera behind player?
    
    def _unlock(self, cam_state: CameraState):
        cam_state.mode = CameraMode.EXPLORATION
        cam_state.target_entity = None
        
    def _validate_lock(self, ctx: PlayerContext):
        """Ensure current target is still valid (alive, in range)."""
        cam_state = ctx.world.get_component(ctx.player_id, CameraState)
        if not cam_state or not cam_state.target_entity:
            return
            
        # Check if target still exists
        target_id = cam_state.target_entity
        transform = ctx.world.get_component(target_id, Transform)
        
        if not transform:
            self._unlock(cam_state)
            return
            
        # Check distance
        dist = (transform.position - ctx.transform.position).length()
        if dist > self.max_lock_distance * 1.2:  # Hysteresis
            print("Target out of range")
            self._unlock(cam_state)

    def _find_best_target(self, ctx: PlayerContext):
        """Find best target based on distance and alignment."""
        player_pos = ctx.transform.position
        
        # Get all entities with Health (potential combat targets)
        # Note: This is an expensive query if many entities exist. 
        target_candidates = ctx.world.get_entities_with(Health, Transform)
        
        best_target = None
        min_score = float('inf')
        
        # Camera forward vector (approximate from base.cam)
        # We need the camera's actual forward vector to pick targets the PLAYER is looking at
        if hasattr(ctx.world, 'base') and ctx.world.base.cam:
            # Get camera quaternion or forward vector
            cam_quat = ctx.world.base.cam.getQuat(ctx.world.base.render)
            cam_forward = cam_quat.getForward()
        else:
            # Fallback (shouldn't happen in normal play)
            cam_forward = LVector3f(0, 1, 0)
        
        for entity_id in target_candidates:
            if entity_id == ctx.player_id:
                continue
                
            transform = ctx.world.get_component(entity_id, Transform)
            if not transform: continue
            
            # Check distance
            to_target = transform.position - player_pos
            dist = to_target.length()
            
            if dist > self.max_lock_distance:
                continue
                
            # Check angle (dot product) to prefer targets in front of camera
            to_target_norm = LVector3f(to_target)
            to_target_norm.normalize()
            
            # Using 2D dot product for horizontal alignment preference? 
            # Or 3D? 3D is fine.
            dot = cam_forward.dot(to_target_norm)
            
            if dot < 0.5: # Must be within ~60 degrees of center
                continue
                
            # Score: Distance / Alignment. Lower is better.
            # We want close targets that are center-screen.
            score = dist / max(0.1, dot * dot)
            
            if score < min_score:
                min_score = score
                best_target = entity_id
                
        return best_target
