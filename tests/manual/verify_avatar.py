
import sys
import os

# Mock panda3d for headless testing if needed, or run with python if environment allows.
# Assuming we can run this in the environment.

from panda3d.core import NodePath, LVector3f
from direct.showbase.ShowBase import ShowBase

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from engine.animation.voxel_avatar import VoxelAvatar
from engine.animation.skeleton import HumanoidSkeleton

def verify_avatar_structure():
    print("🧪 Verifying VoxelAvatar Structure...")
    
    # Setup minimal Panda3D environment (headless)
    base = ShowBase(windowType='offscreen')
    
    skeleton = HumanoidSkeleton()
    avatar = VoxelAvatar(base.render, skeleton)
    
    print(f"✅ Created VoxelAvatar with root: {avatar.root}")
    
    # Check bone nodes exist
    expected_bones = ['hips', 'spine', 'chest', 'head', 'upper_arm_left', 'hand_right', 'foot_left']
    for bone in expected_bones:
        if bone in avatar.bone_nodes:
            print(f"  ✅ Found visual node for: {bone}")
        else:
            print(f"  ❌ Missing visual node for: {bone}")
            
    # Check hierarchy
    # We decided on a flat hierarchy under root for VoxelAvatar visuals?
    # Let's check parent of a bone node.
    chest_node = avatar.bone_nodes['chest']
    parent = chest_node.getParent()
    print(f"  ℹ️ Parent of chest is: {parent.getName()}")
    
    if parent == avatar.root:
        print("  ✅ Hierarchy is flat (children of root) as expected for World Transform application.")
    else:
        print("  ❓ Hierarchy is nested/unexpected.")

    base.destroy()

if __name__ == "__main__":
    verify_avatar_structure()
