"""Animation mechanic for player mannequin with layered combat animations."""

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from panda3d.core import LVector3f
from typing import Optional
import math

class AnimationMechanic(PlayerMechanic):
    """Handles player avatar rendering and layered animations.
    
    Uses LayeredAnimator to composite:
    - Locomotion layer (full body): walk/idle/jump
    - Combat layer (upper body): attacks/parry
    - Combat layer (full body): dodge
    """
    
    priority = 5  # Run last (after movement and camera)
    exclusive = False
    
    def __init__(self, base):
        self.base = base
        # Renamed to avatar, but keeping local_mannequin alias if needed by others?
        # Actually it's internal, so we can rename.
        self.avatar = None 
        self.layered_animator = None
        self.locomotion_source = None
        self.combat_source = None
        self.root_motion_applicator = None
        
        # Track previous combat state for transition detection
        self.previous_combat_state = "idle"
        self.dodge_direction = LVector3f(0, 1, 0)  # Default forward
    
    def initialize(self, player_id, world):
        """Called when player is ready."""
        try:
            from engine.animation.voxel_avatar import VoxelAvatar
            from engine.animation.mannequin import AnimationController
            from engine.animation.layers import LayeredAnimator, BoneMask
            from engine.animation.sources import ProceduralAnimationSource
            from engine.animation.root_motion import RootMotionApplicator
            from engine.player_mechanics.combat_animation_source import CombatAnimationSource
            
            # Create the avatar (visuals)
            self.avatar = VoxelAvatar(
                self.base.render, 
                body_color=(0.2, 0.8, 0.2, 1.0)  # Greenish for local player
            )
            
            # Create base animation controller for locomotion
            # Note: AnimationController still expects "mannequin" for backward compat properties?
            # We might need to update AnimationController or wrap VoxelAvatar to look like Mannequin if Controller uses properties.
            # Checking AnimationController: uses self.mannequin.right_arm_pivot which maps to bone_nodes['upper_arm_right'].
            # VoxelAvatar has .bone_nodes.
            # But AnimationController also has logic like `mannequin._walk_phase`.
            # We'll need to patch/update AnimationController or add those props to VoxelAvatar.
            # VoxelAvatar is pure visual. AnimationController holds state.
            
            # Temporary: Monkey-patch state onto avatar for AnimationController compatibility
            self.avatar._walk_phase = 0.0
            self.avatar._idle_time = 0.0
            
            # Also AnimationController expects `mannequin.right_arm_pivot` etc.
            # VoxelAvatar doesn't have those properties.
            # We should probably update AnimationController to use bone names directly, or add properties to VoxelAvatar.
            # For this step, let's update AnimationController imports in a separate tool call if needed, 
            # Or assume we can access bones directly.
            
            # Wait, AnimationController takes a 'mannequin' argument.
            # Let's inspect AnimationController again. It calls `self.mannequin.right_arm_pivot`.
            # We should probably use a subclass or update AnimationController.
            # Or we can just attach the properties to VoxelAvatar instance dynamically?
            # Or better: Update AnimationController to use skeleton/bone_nodes directly.
            
            # Actually, to avoid breaking everything, let's stick to Mannequin logic for Locomotion for a second?
            # No, user wants VoxelAvatar.
            # Let's add compatibility properties to VoxelAvatar in a monkey-patch style here to keep it working,
            # OR better, update `AnimationMechanic`'s use of sources.
            # `ProceduralAnimationSource` uses `AnimationController`.
            
            # Let's rely on VoxelAvatar having `bone_nodes`.
            # We will use a compatibility wrapper for AnimationController?
            # See below `_AvatarAdapter`.
            
            # Create layered animator
            self.layered_animator = LayeredAnimator(self.avatar.skeleton)
            
            # Create animation sources
            # We need an AnimationController that works with VoxelAvatar.
            # Since we can't easily rewrite AnimationController right this second without a new file or reading it again,
            # Let's use a wrapper or just accept we might need to fix AnimationController next.
            # Actually, `ProceduralAnimationSource` uses `AnimationController`.
            # `AnimationController` uses `AnimatedMannequin`.
            
            # Let's pass a mock/adapter to AnimationController if needed.
            class AvatarAdapter:
                def __init__(self, avatar):
                    self.avatar = avatar
                    self._walk_phase = 0.0
                    self._idle_time = 0.0
                    self.root = avatar.root # For setZ in idle
                    self.torso = avatar.bone_nodes.get('chest') 
                    
                    # Map properties
                
                @property
                def right_arm_pivot(self): return self.avatar.bone_nodes.get('upper_arm_right')
                @property
                def left_arm_pivot(self): return self.avatar.bone_nodes.get('upper_arm_left')
                @property
                def right_leg_pivot(self): return self.avatar.bone_nodes.get('thigh_right')
                @property
                def left_leg_pivot(self): return self.avatar.bone_nodes.get('thigh_left')
                
            adapter = AvatarAdapter(self.avatar)
            
            base_controller = AnimationController(adapter) # Type ignore
            
            self.locomotion_source = ProceduralAnimationSource(base_controller)
            self.combat_source = CombatAnimationSource()
            
            # Add locomotion layer (base layer, full body)
            self.layered_animator.add_layer(
                name="locomotion",
                source=self.locomotion_source,
                priority=0,  # Lower priority (applied first)
                weight=1.0,
                mask=BoneMask.full_body()
            )
            
            # Add combat layer (overlay layer, upper body for attacks/parry)
            self.layered_animator.add_layer(
                name="combat",
                source=self.combat_source,
                priority=10,  # Higher priority (applied second, overrides upper body)
                weight=1.0,
                mask=BoneMask.upper_body()
            )
            
            # Create root motion applicator
            self.root_motion_applicator = RootMotionApplicator()
            
            print("✅ AnimationMechanic: VoxelAvatar & Layered animation initialized")
            
        except ImportError as e:
            print(f"❌ AnimationMechanic: Animation system error: {e}")
            self.avatar = None
        except Exception as e:
            print(f"❌ AnimationMechanic: Unexpected error creating avatar: {e}")
            import traceback
            traceback.print_exc()
            self.avatar = None
            
    def update(self, ctx: PlayerContext) -> None:
        if not self.avatar or not self.layered_animator:
            return
            
        # 1. Handle Visibility based on Camera Mode
        from engine.components.camera_state import CameraState, CameraMode
        camera_state = ctx.world.get_component(ctx.player_id, CameraState)
        
        if camera_state and camera_state.mode == CameraMode.FIRST_PERSON:
            if self.avatar.root.isHidden() == False:
                # print(f"👻 Hiding avatar (first-person mode)")
                pass
            self.avatar.root.hide()
            return  # No need to update animations if invisible
        else:
            if self.avatar.root.isHidden():
                # print(f"👁️ Showing avatar (third-person mode)")
                pass
            self.avatar.root.show()
            
        # 2. Sync Position
        self.avatar.root.setPos(ctx.transform.position)
        
        # 3. Sync Rotation
        cam_yaw = self.base.cam.getH()
        self.avatar.root.setH(cam_yaw)
        
        # 4. Update Combat State and Trigger Animations
        from engine.components.core import CombatState
        combat_state = ctx.world.get_component(ctx.player_id, CombatState)
        
        if combat_state:
            self._handle_combat_animations(combat_state, ctx)
        
        # 5. Update Locomotion Layer
        velocity = LVector3f(
            ctx.state.velocity_x, 
            ctx.state.velocity_y, 
            ctx.state.velocity_z
        )
        self.locomotion_source.set_movement_state(velocity, ctx.state.grounded)
        
        # 6. Update Layered Animator
        self.layered_animator.update(ctx.dt)
        
        # Apply skeleton transforms to avatar bone nodes
        self.layered_animator.apply_to_skeleton()
        self._apply_skeleton_to_avatar()
        
        # 7. Apply Root Motion (if combat animation is playing)
        if self.combat_source.is_playing():
            current_clip = self.combat_source.get_current_clip()
            if current_clip and hasattr(current_clip, 'root_motion') and current_clip.root_motion:
                # Apply root motion to kinematic state
                self.root_motion_applicator.extract_and_apply(
                    clip=current_clip,
                    current_time=self.combat_source.current_time,
                    dt=ctx.dt,
                    kinematic_state=ctx.state,
                    character_rotation=cam_yaw
                )
    
    def _handle_combat_animations(self, combat_state: 'CombatState', ctx: PlayerContext):
        """Handle combat state transitions and trigger appropriate animations.
        
        Args:
            combat_state: Current combat state component
            ctx: Player context
        """
        current_state = combat_state.state
        
        # Detect state transitions
        if current_state != self.previous_combat_state:
            self._on_combat_state_changed(current_state, ctx)
            self.previous_combat_state = current_state
        
        # Update combat layer bone mask based on state
        from engine.animation.layers import BoneMask
        if current_state == "dodging":
            self.layered_animator.get_layer("combat").mask = BoneMask.full_body()
        else:
            self.layered_animator.get_layer("combat").mask = BoneMask.upper_body()
    
    def _on_combat_state_changed(self, new_state: str, ctx: PlayerContext):
        """Handle combat state transition."""
        if new_state == "attacking":
            # print("⚔️ Playing attack animation")
            self.combat_source.play("sword_slash")
            
        elif new_state == "dodging":
            # print("🏃 Playing dodge animation")
            self.dodge_direction = self._calculate_dodge_direction(ctx)
            # Future: Apply dodge direction
            self.combat_source.play("dodge")
            
        elif new_state == "parrying":
            # print("🛡️ Playing parry animation")
            self.combat_source.play("parry_start")
            
        elif new_state == "idle":
            if self.combat_source.is_playing():
                self.combat_source.stop()
    
    def _apply_skeleton_to_avatar(self):
        """Apply skeleton bone transforms to avatar visual nodes.
        
        Uses LOCAL transforms because VoxelAvatar nodes are now hierarchical.
        Panda3D automatically handles world transform propagation.
        """
        for bone_name, node in self.avatar.bone_nodes.items():
            bone = self.avatar.skeleton.get_bone(bone_name)
            if not bone:
                continue
            
            # Use LOCAL transform (relative to parent)
            # The bone_nodes hierarchy mirrors the skeleton hierarchy
            transform = bone.local_transform
            
            # Apply position and rotation
            # Note: Skeleton positions are offsets from parent joint
            node.setPos(transform.position)
            node.setHpr(
                transform.rotation.x,  # heading
                transform.rotation.y,  # pitch  
                transform.rotation.z   # roll
            )
    
    def _calculate_dodge_direction(self, ctx: PlayerContext) -> LVector3f:
        """Calculate dodge direction from input state."""
        cam_yaw = self.base.cam.getH()
        cam_yaw_rad = math.radians(cam_yaw)
        
        forward = LVector3f(-math.sin(cam_yaw_rad), math.cos(cam_yaw_rad), 0)
        right = LVector3f(math.cos(cam_yaw_rad), math.sin(cam_yaw_rad), 0)
        
        direction = LVector3f(0, 0, 0)
        
        if ctx.input.forward: direction += forward
        if ctx.input.back: direction -= forward
        if ctx.input.right: direction += right
        if ctx.input.left: direction -= right
        
        if direction.length() < 0.1:
            direction = forward
        else:
            direction.normalize()
        
        return direction
            
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.avatar:
            self.avatar.cleanup()
            self.avatar = None
        self.layered_animator = None
        self.locomotion_source = None
        self.combat_source = None
        self.root_motion_applicator = None

