
from panda3d.core import LVector3f, LQuaternionf, NodePath
from direct.showbase.ShowBase import ShowBase

def test_rotations():
    print("Testing Rotations for Bone Alignment (Y-axis to Target)")
    
    # Standard Y-axis vector
    y_axis = LVector3f(0, 1, 0)
    
    # 1. Spine (Target: +Z)
    # Rotate around X by -90?
    rot_spine = NodePath("spine")
    rot_spine.setHpr(0, -90, 0) # Pitch -90
    result = rot_spine.getQuat().xform(y_axis)
    print(f"Spine (Pitch -90): Y-axis maps to {result} (Target: 0, 0, 1)")
    
    # 2. Right Arm (Target: +X)
    # Rotate around Z by -90?
    rot_r_arm = NodePath("r_arm")
    rot_r_arm.setHpr(-90, 0, 0) # Heading -90
    result = rot_r_arm.getQuat().xform(y_axis)
    print(f"Right Arm (Heading -90): Y-axis maps to {result} (Target: 1, 0, 0)")
    
    # 3. Left Arm (Target: -X)
    rot_l_arm = NodePath("l_arm")
    rot_l_arm.setHpr(90, 0, 0) # Heading 90
    result = rot_l_arm.getQuat().xform(y_axis)
    print(f"Left Arm (Heading 90): Y-axis maps to {result} (Target: -1, 0, 0)")
    
    # 4. Legs (Target: -Z)
    rot_leg = NodePath("leg")
    rot_leg.setHpr(0, 90, 0) # Pitch 90
    result = rot_leg.getQuat().xform(y_axis)
    print(f"Leg (Pitch 90): Y-axis maps to {result} (Target: 0, 0, -1)")
    
if __name__ == "__main__":
    test_rotations()
