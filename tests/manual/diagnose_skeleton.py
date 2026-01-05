"""
Quick diagnostic script to check skeleton state at runtime.
Run with: python3 tests/manual/diagnose_skeleton.py
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import LVector3f
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.animation.skeleton import HumanoidSkeleton
from engine.animation.voxel_avatar import VoxelAvatar
from engine.animation.layers import LayeredAnimator
from engine.animation.sources import ProceduralAnimationSource
from engine.animation.mannequin import AnimationController

class DiagnosticApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self, windowType='offscreen')
        
        print("\n" + "="*70)
        print("SKELETON DIAGNOSTIC")
        print("="*70)
        
        # Create skeleton
        skeleton = HumanoidSkeleton()
        
        print("\n1. INITIAL SKELETON STATE (after _set_default_pose)")
        print("-" * 70)
        self.print_bone_state(skeleton, "hips")
        self.print_bone_state(skeleton, "thigh_left")
        self.print_bone_state(skeleton, "shin_left")
        
        # Create avatar
        avatar = VoxelAvatar(self.render, skeleton)
        
        # Create animation system
        class DummyAdapter:
            def __init__(self, avatar):
                self.avatar = avatar
                self._walk_phase = 0.0
                self._idle_time = 0.0
                self.root = avatar.root
                self.torso = avatar.bone_nodes.get('chest')
            @property
            def right_arm_pivot(self): return self.avatar.bone_nodes.get('upper_arm_right')
            @property
            def left_arm_pivot(self): return self.avatar.bone_nodes.get('upper_arm_left')
            @property
            def right_leg_pivot(self): return self.avatar.bone_nodes.get('thigh_right')
            @property
            def left_leg_pivot(self): return self.avatar.bone_nodes.get('thigh_left')
        
        adapter = DummyAdapter(avatar)
        controller = AnimationController(adapter)
        
        locomotion_source = ProceduralAnimationSource(controller)
        locomotion_source.set_movement_state(LVector3f(0, 0, 0), True)  # Idle
        
        animator = LayeredAnimator(skeleton)
        animator.add_layer("locomotion", locomotion_source, priority=0)
        
        print("\n2. AFTER ANIMATION SETUP (before update)")
        print("-" * 70)
        self.print_bone_state(skeleton, "hips")
        self.print_bone_state(skeleton, "thigh_left")
        
        # Run one animation update
        animator.update(0.016)
        animator.apply_to_skeleton()
        
        print("\n3. AFTER FIRST ANIMATION UPDATE")
        print("-" * 70)
        self.print_bone_state(skeleton, "hips")
        self.print_bone_state(skeleton, "thigh_left")
        self.print_bone_state(skeleton, "shin_left")
        
        # Check what was in the pose
        print("\n4. BONES IN LAST POSE")
        print("-" * 70)
        last_pose = animator.get_last_pose()
        print(f"Bones animated: {list(last_pose.keys())}")
        if 'hips' in last_pose:
            print(f"  hips: pos={last_pose['hips'].position}, rot={last_pose['hips'].rotation}")
        if 'thigh_left' in last_pose:
            print(f"  thigh_left: pos={last_pose['thigh_left'].position}, rot={last_pose['thigh_left'].rotation}")
        
        print("\n" + "="*70)
        print("DIAGNOSTIC COMPLETE")
        print("="*70 + "\n")
        
        self.destroy()
    
    def print_bone_state(self, skeleton, bone_name):
        bone = skeleton.get_bone(bone_name)
        if not bone:
            print(f"  {bone_name}: NOT FOUND")
            return
        
        print(f"  {bone_name}:")
        print(f"    local_transform.position: {bone.local_transform.position}")
        print(f"    local_transform.rotation: {bone.local_transform.rotation}")
        print(f"    rest_transform.position:  {bone.rest_transform.position}")
        print(f"    rest_transform.rotation:  {bone.rest_transform.rotation}")

if __name__ == "__main__":
    app = DiagnosticApp()
