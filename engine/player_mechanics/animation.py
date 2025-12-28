"""Animation mechanic for player mannequin with layered combat animations."""

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from panda3d.core import LVector3f
from typing import Optional
import math

class AnimationMechanic(PlayerMechanic):
    """Handles player mannequin rendering and layered animations.
    
    Uses LayeredAnimator to composite:
    - Locomotion layer (full body): walk/idle/jump
    - Combat layer (upper body): attacks/parry
    - Combat layer (full body): dodge
    """
    
    priority = 5  # Run last (after movement and camera)
    exclusive = False
    
    def __init__(self, base):
        self.base = base
        self.local_mannequin = None
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
            from engine.animation.mannequin import AnimatedMannequin, AnimationController
            from engine.animation.layers import LayeredAnimator, BoneMask
            from engine.animation.sources import ProceduralAnimationSource
            from engine.animation.root_motion import RootMotionApplicator
            from engine.player_mechanics.combat_animation_source import CombatAnimationSource
            
            # Create the mannequin (visuals)
            self.local_mannequin = AnimatedMannequin(
                self.base.render, 
                body_color=(0.2, 0.8, 0.2, 1.0)  # Greenish for local player
            )
            
            # Create base animation controller for locomotion
            base_controller = AnimationController(self.local_mannequin)
            
            # Create layered animator
            self.layered_animator = LayeredAnimator(self.local_mannequin.skeleton)
            
            # Create animation sources
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
            
            print("✅ AnimationMechanic: Layered animation system initialized")
            
        except ImportError as e:
            print(f"❌ AnimationMechanic: Animation system error: {e}")
            self.local_mannequin = None
        except Exception as e:
            print(f"❌ AnimationMechanic: Unexpected error creating mannequin: {e}")
            import traceback
            traceback.print_exc()
            self.local_mannequin = None
            
    def update(self, ctx: PlayerContext) -> None:
        if not self.local_mannequin or not self.layered_animator:
            return
            
        # 1. Handle Visibility based on Camera Mode
        from engine.components.camera_state import CameraState, CameraMode
        camera_state = ctx.world.get_component(ctx.player_id, CameraState)
        
        if camera_state and camera_state.mode == CameraMode.FIRST_PERSON:
            if self.local_mannequin.root.isHidden() == False:
                print(f"👻 Hiding mannequin (first-person mode)")
            self.local_mannequin.root.hide()
            return  # No need to update animations if invisible
        else:
            if self.local_mannequin.root.isHidden():
                print(f"👁️ Showing mannequin (third-person mode)")
            self.local_mannequin.root.show()
            
        # 2. Sync Position
        self.local_mannequin.root.setPos(ctx.transform.position)
        
        # 3. Sync Rotation
        cam_yaw = self.base.cam.getH()
        self.local_mannequin.root.setH(cam_yaw)
        
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
        
        # Apply skeleton transforms to mannequin bone nodes
        self.layered_animator.apply_to_skeleton()
        self._apply_skeleton_to_mannequin()
        
        # 7. Apply Root Motion (if combat animation is playing)
        if self.combat_source.is_playing():
            current_clip = self.combat_source.get_current_clip()
            if current_clip and current_clip.root_motion:
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
        # Dodge uses full body, attacks/parry use upper body
        from engine.animation.layers import BoneMask
        if current_state == "dodging":
            self.layered_animator.get_layer("combat").mask = BoneMask.full_body()
        else:
            self.layered_animator.get_layer("combat").mask = BoneMask.upper_body()
    
    def _on_combat_state_changed(self, new_state: str, ctx: PlayerContext):
        """Handle combat state transition.
        
        Args:
            new_state: New combat state
            ctx: Player context
        """
        if new_state == "attacking":
            print("⚔️ Playing attack animation")
            self.combat_source.play("sword_slash")
            
        elif new_state == "dodging":
            print("🏃 Playing dodge animation")
            # Calculate dodge direction from input
            self.dodge_direction = self._calculate_dodge_direction(ctx)
            # TODO: Apply dodge direction to root motion curve
            self.combat_source.play("dodge")
            
        elif new_state == "parrying":
            print("🛡️ Playing parry animation")
            self.combat_source.play("parry_start")
            
        elif new_state == "idle":
            # Return to locomotion only
            if self.combat_source.is_playing():
                self.combat_source.stop()
    
    
    
    def _apply_skeleton_to_mannequin(self):
        """Apply skeleton bone transforms to mannequin visual nodes.
        
        The LayeredAnimator works with the Skeleton abstraction, but we need
        to apply those transforms to the actual Panda3D NodePaths for rendering.
        """
        # CRITICAL: Apply transforms for ALL bones that have visual nodes,
        # not just bones being animated. This ensures all body parts are visible.
        for bone_name in self.local_mannequin.bone_nodes.keys():
            node = self.local_mannequin.bone_nodes[bone_name]
            
            # Get bone from skeleton (all bones exist in skeleton)
            bone = self.local_mannequin.skeleton.get_bone(bone_name)
            if not bone:
                continue
            
            # Use WORLD transform for rotation
            # The visual nodes are children of the character root, so they need
            # rotation in character space (which bone.world_transform provides).
            transform = bone.world_transform
            
            # Apply transform to node
            # Note: Panda3D uses setHpr for rotation (heading, pitch, roll)
            node.setHpr(
                transform.rotation.x,  # heading
                transform.rotation.y,  # pitch  
                transform.rotation.z   # roll
            )
            
            # Position Handling:
            # We currently IGNORE skeleton positions because:
            # 1. The skeleton dimensions (spine length 0.8) don't match visual mannequin (chest gap 0.3)
            # 2. Applying positions causes "floating torso" issues due to mismatched offsets
            # 
            # Ideally we would retarget or align them, but for now, preserving the 
            # visual model's built-in proportions and only animating rotation is 
            # the most robust solution.
            
            # if transform.position.length() > 0.01:
            #    base_pos = self._get_bone_base_position(bone_name)
            #    node.setPos(base_pos + transform.position)
    
    def _get_bone_base_position(self, bone_name: str) -> LVector3f:
        """Get the base/default position for a bone's visual node.
        
        Args:
            bone_name: Name of the bone
            
        Returns:
            Base position vector
        """
        # These match the positions set in AnimatedMannequin._build_body()
        base_positions = {
            'head': LVector3f(0, 0, 1.6),
            'chest': LVector3f(0, 0, 1.1),
            'upper_arm_right': LVector3f(0.28, 0, 1.35),
            'upper_arm_left': LVector3f(-0.28, 0, 1.35),
            'thigh_right': LVector3f(0.1, 0, 0.8),
            'thigh_left': LVector3f(-0.1, 0, 0.8),
        }
        return base_positions.get(bone_name, LVector3f(0, 0, 0))
    
    def _calculate_dodge_direction(self, ctx: PlayerContext) -> LVector3f:
        """Calculate dodge direction from input state.
        
        Args:
            ctx: Player context with input state
            
        Returns:
            Normalized direction vector in world space
        """
        # Get camera heading for direction calculation
        cam_yaw = self.base.cam.getH()
        cam_yaw_rad = math.radians(cam_yaw)
        
        # Calculate forward and right vectors based on camera
        forward = LVector3f(-math.sin(cam_yaw_rad), math.cos(cam_yaw_rad), 0)
        right = LVector3f(math.cos(cam_yaw_rad), math.sin(cam_yaw_rad), 0)
        
        # Build direction from input
        direction = LVector3f(0, 0, 0)
        
        if ctx.input.forward:
            direction += forward
        if ctx.input.back:
            direction -= forward
        if ctx.input.right:
            direction += right
        if ctx.input.left:
            direction -= right
        
        # Default to forward if no input
        if direction.length() < 0.1:
            direction = forward
        else:
            direction.normalize()
        
        return direction
            
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.local_mannequin:
            self.local_mannequin.cleanup()
            self.local_mannequin = None
            self.layered_animator = None
            self.locomotion_source = None
            self.combat_source = None
            self.root_motion_applicator = None
