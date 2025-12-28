"""Tests for skeleton system."""

import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock panda3d
from unittest.mock import MagicMock

mock_panda = MagicMock()
mock_core = MagicMock()

class MockVector3:
    def __init__(self, x=0, y=0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, other):
        return MockVector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return MockVector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return MockVector3(self.x * other, self.y * other, self.z * other)
        return MockVector3(self.x * other.x, self.y * other.y, self.z * other.z)
    
    def __repr__(self):
        return f"MockVector3({self.x}, {self.y}, {self.z})"

class MockNodePath:
    def __init__(self, name="node"):
        self.name = name
        self.pos = MockVector3(0, 0, 0)
        self.hpr = MockVector3(0, 0, 0)
        self.scale = MockVector3(1, 1, 1)
    
    def setPos(self, *args):
        if len(args) == 1:
            self.pos = args[0]
        elif len(args) == 3:
            self.pos = MockVector3(*args)
    
    def setHpr(self, *args):
        if len(args) == 1:
            self.hpr = args[0]
        elif len(args) == 3:
            self.hpr = MockVector3(*args)
    
    def setScale(self, *args):
        if len(args) == 1:
            self.scale = args[0]
        elif len(args) == 3:
            self.scale = MockVector3(*args)

mock_core.NodePath = MockNodePath
mock_core.LVector3f = MockVector3
mock_core.LQuaternionf = MagicMock
sys.modules['panda3d'] = mock_panda
sys.modules['panda3d.core'] = mock_core

# Import after mocking
from engine.animation.skeleton import Bone, Skeleton, HumanoidSkeleton, BoneConstraints


class TestBoneConstraints(unittest.TestCase):
    """Test bone rotation constraints."""
    
    def test_default_constraints_clamp_to_plus_minus_180(self):
        """Default constraints clamp to ±180 degrees."""
        constraints = BoneConstraints()
        h, p, r = constraints.clamp(270, 170, -90)
        self.assertEqual(h, 180)  # Clamped to max_h
        self.assertEqual(p, 170)  # Within range
        self.assertEqual(r, -90)  # Within range
    
    def test_constraints_clamp_min_angles(self):
        """Constraints should clamp to minimum values."""
        constraints = BoneConstraints(min_p=-45, max_p=45)
        h, p, r = constraints.clamp(0, -60, 0)
        self.assertEqual(p, -45)
    
    def test_constraints_clamp_max_angles(self):
        """Constraints should clamp to maximum values."""
        constraints = BoneConstraints(min_p=-45, max_p=45)
        h, p, r = constraints.clamp(0, 60, 0)
        self.assertEqual(p, 45)


class TestBone(unittest.TestCase):
    """Test individual bone functionality."""
    
    def test_bone_initialization(self):
        """Bone should initialize with correct attributes."""
        bone = Bone("test_bone", length=1.5)
        self.assertEqual(bone.name, "test_bone")
        self.assertEqual(bone.length, 1.5)
        self.assertIsNone(bone.parent)
        self.assertEqual(len(bone.children), 0)
    
    def test_bone_parent_child_relationship(self):
        """Child bone should auto-register with parent."""
        parent = Bone("parent", length=1.0)
        child = Bone("child", length=0.5, parent=parent)
        
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children)
    
    def test_set_local_rotation_applies_constraints(self):
        """set_local_rotation should respect constraints by default."""
        constraints = BoneConstraints(min_p=-45, max_p=45)
        bone = Bone("elbow", length=1.0, constraints=constraints)
        
        bone.set_local_rotation(0, 90, 0, apply_constraints=True)
        self.assertEqual(bone.local_transform.rotation.y, 45)  # Clamped
    
    def test_set_local_rotation_can_skip_constraints(self):
        """set_local_rotation can bypass constraints if requested."""
        constraints = BoneConstraints(min_p=-45, max_p=45)
        bone = Bone("elbow", length=1.0, constraints=constraints)
        
        bone.set_local_rotation(0, 90, 0, apply_constraints=False)
        self.assertEqual(bone.local_transform.rotation.y, 90)  # Not clamped


class TestSkeleton(unittest.TestCase):
    """Test skeleton hierarchy management."""
    
    def test_skeleton_initialization_creates_root(self):
        """Skeleton should create root bone on init."""
        skeleton = Skeleton(root_name="hips")
        self.assertIsNotNone(skeleton.root)
        self.assertEqual(skeleton.root.name, "hips")
        self.assertIn("hips", skeleton.bones)
    
    def test_add_bone_creates_hierarchy(self):
        """add_bone should create parent-child relationships."""
        skeleton = Skeleton()
        spine = skeleton.add_bone("spine", "root", length=1.0)
        
        self.assertIn("spine", skeleton.bones)
        self.assertEqual(spine.parent, skeleton.root)
        self.assertIn(spine, skeleton.root.children)
    
    def test_add_bone_with_invalid_parent_raises(self):
        """add_bone should raise if parent doesn't exist."""
        skeleton = Skeleton()
        
        with self.assertRaises(ValueError):
            skeleton.add_bone("orphan", "nonexistent", length=1.0)
    
    def test_add_duplicate_bone_raises(self):
        """add_bone should raise if name already exists."""
        skeleton = Skeleton()
        skeleton.add_bone("spine", "root", length=1.0)
        
        with self.assertRaises(ValueError):
            skeleton.add_bone("spine", "root", length=1.0)
    
    def test_get_bone_retrieves_by_name(self):
        """get_bone should retrieve bone by name."""
        skeleton = Skeleton()
        spine = skeleton.add_bone("spine", "root", length=1.0)
        
        retrieved = skeleton.get_bone("spine")
        self.assertEqual(retrieved, spine)
    
    def test_get_bone_returns_none_for_missing(self):
        """get_bone should return None if bone doesn't exist."""
        skeleton = Skeleton()
        self.assertIsNone(skeleton.get_bone("missing"))
    
    def test_get_chain_returns_path(self):
        """get_chain should return bone path from root to tip."""
        skeleton = Skeleton()
        skeleton.add_bone("spine", "root", length=1.0)
        skeleton.add_bone("chest", "spine", length=0.8)
        skeleton.add_bone("head", "chest", length=0.5)
        
        chain = skeleton.get_chain("spine", "head")
        
        self.assertEqual(len(chain), 3)
        self.assertEqual(chain[0].name, "spine")
        self.assertEqual(chain[1].name, "chest")
        self.assertEqual(chain[2].name, "head")
    
    def test_get_chain_raises_if_not_connected(self):
        """get_chain should raise if bones aren't in same hierarchy."""
        skeleton = Skeleton()
        skeleton.add_bone("arm", "root", length=1.0)
        skeleton.add_bone("leg", "root", length=1.0)
        
        with self.assertRaises(ValueError):
            skeleton.get_chain("arm", "leg")


class TestHumanoidSkeleton(unittest.TestCase):
    """Test humanoid skeleton preset."""
    
    def test_humanoid_skeleton_has_all_bones(self):
        """HumanoidSkeleton should create all 17 bones."""
        skeleton = HumanoidSkeleton()
        
        expected_bones = [
            "hips", "spine", "chest", "head",
            "shoulder_left", "upper_arm_left", "forearm_left", "hand_left",
            "shoulder_right", "upper_arm_right", "forearm_right", "hand_right",
            "thigh_left", "shin_left", "foot_left",
            "thigh_right", "shin_right", "foot_right"
        ]
        
        for bone_name in expected_bones:
            self.assertIn(bone_name, skeleton.bones,
                         f"Missing bone: {bone_name}")
        
        # Should have exactly 18 bones (including hips root)
        self.assertEqual(len(skeleton.bones), 18)
    
    def test_humanoid_skeleton_arm_chains(self):
        """Arm chains should be connected correctly."""
        skeleton = HumanoidSkeleton()
        
        # Left arm chain
        left_chain = skeleton.get_chain("shoulder_left", "hand_left")
        self.assertEqual(len(left_chain), 4)
        
        # Right arm chain
        right_chain = skeleton.get_chain("shoulder_right", "hand_right")
        self.assertEqual(len(right_chain), 4)
    
    def test_humanoid_skeleton_leg_chains(self):
        """Leg chains should be connected correctly."""
        skeleton = HumanoidSkeleton()
        
        # Left leg chain
        left_chain = skeleton.get_chain("thigh_left", "foot_left")
        self.assertEqual(len(left_chain), 3)
        
        # Right leg chain
        right_chain = skeleton.get_chain("thigh_right", "foot_right")
        self.assertEqual(len(right_chain), 3)
    
    def test_humanoid_skeleton_has_constraints(self):
        """Key joints should have rotation constraints."""
        skeleton = HumanoidSkeleton()
        
        # Elbow should only bend one way
        forearm_left = skeleton.get_bone("forearm_left")
        self.assertEqual(forearm_left.constraints.min_p, 0)
        self.assertEqual(forearm_left.constraints.max_p, 150)
        
        # Knee should only bend backward
        shin_left = skeleton.get_bone("shin_left")
        self.assertEqual(shin_left.constraints.min_p, -150)
        self.assertEqual(shin_left.constraints.max_p, 0)
    
    def test_humanoid_skeleton_spine_chain(self):
        """Spine chain should connect hips to head."""
        skeleton = HumanoidSkeleton()
        
        chain = skeleton.get_chain("hips", "head")
        self.assertEqual(len(chain), 4)  # hips -> spine -> chest -> head
        self.assertEqual(chain[0].name, "hips")
        self.assertEqual(chain[-1].name, "head")


if __name__ == '__main__':
    unittest.main()
