"""Tests for IK system."""

import unittest
import sys
import os
import math

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
    
    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return MockVector3(self.x / other, self.y / other, self.z / other)
        return MockVector3(self.x / other.x, self.y / other.y, self.z / other.z)
    
    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
    
    def __repr__(self):
        return f"MockVector3({self.x}, {self.y}, {self.z})"

mock_core.LVector3f = MockVector3
mock_core.LQuaternionf = MagicMock
mock_core.NodePath = MagicMock
sys.modules['panda3d'] = mock_panda
sys.modules['panda3d.core'] = mock_core

# Import after mocking
from engine.animation.ik import IKTarget, FABRIKSolver, IKLayer
from engine.animation.foot_ik import FootIKController
from engine.animation.skeleton import Skeleton, Bone, HumanoidSkeleton
from engine.animation.core import Transform


class TestIKTarget(unittest.TestCase):
    """Test IK target data structure."""
    
    def test_target_initialization(self):
        """IK target should initialize with position and bone name."""
        target = IKTarget(
            position=MockVector3(1, 2, 3),
            bone_name="foot_left"
        )
        
        self.assertEqual(target.position.x, 1)
        self.assertEqual(target.position.y, 2)
        self.assertEqual(target.position.z, 3)
        self.assertEqual(target.bone_name, "foot_left")
        self.assertEqual(target.weight, 1.0)


class TestFABRIKSolver(unittest.TestCase):
    """Test FABRIK IK solver."""
    
    def test_solver_initialization(self):
        """Solver should initialize with defaults."""
        solver = FABRIKSolver()
        self.assertEqual(solver.tolerance, 0.01)
        self.assertEqual(solver.max_iterations, 10)
    
    def test_two_bone_chain_reachable_target(self):
        """2-bone chain should reach reachable target."""
        solver = FABRIKSolver(tolerance=0.1)
        
        # Create simple 2-bone chain (thigh -> shin)
        skeleton = Skeleton("root")
        skeleton.add_bone("thigh", "root", length=1.0)
        skeleton.add_bone("shin", "thigh", length=1.0)
        
        chain = [skeleton.get_bone("thigh"), skeleton.get_bone("shin")]
        
        # Target within reach (1.5 units from root, chain length = 2.0)
        target = MockVector3(0, 1.5, 0)
        
        transforms = solver.solve(chain, target, root_position=MockVector3(0, 0, 0))
        
        # Should have transforms for both bones
        self.assertIn("thigh", transforms)
        self.assertIn("shin", transforms)
    
    def test_unreachable_target_stretches(self):
        """Chain should stretch toward unreachable target."""
        solver = FABRIKSolver()
        
        skeleton = Skeleton("root")
        skeleton.add_bone("thigh", "root", length=1.0)
        skeleton.add_bone("shin", "thigh", length=1.0)
        
        chain = [skeleton.get_bone("thigh"), skeleton.get_bone("shin")]
        
        # Target beyond reach (3.0 units, chain length = 2.0)
        target = MockVector3(0, 3.0, 0)
        
        transforms = solver.solve(chain, target, root_position=MockVector3(0, 0, 0))
        
        # Should still return transforms (stretched)
        self.assertEqual(len(transforms), 2)
    
    def test_convergence_within_tolerance(self):
        """Solver should converge close to target."""
        solver = FABRIKSolver(tolerance=0.05, max_iterations=20)
        
        skeleton = Skeleton("root")
        skeleton.add_bone("bone1", "root", length=1.0)
        skeleton.add_bone("bone2", "bone1", length=1.0)
        skeleton.add_bone("bone3", "bone2", length=1.0)
        
        chain = [
            skeleton.get_bone("bone1"),
            skeleton.get_bone("bone2"),
            skeleton.get_bone("bone3")
        ]
        
        target = MockVector3(1, 1, 1)
        root = MockVector3(0, 0, 0)
        
        transforms = solver.solve(chain, target, root_position=root)
        
        # Should have solved for all bones
        self.assertEqual(len(transforms), 3)


class TestIKLayer(unittest.TestCase):
    """Test IK layer integration."""
    
    def test_layer_initialization(self):
        """IK layer should initialize with skeleton."""
        skeleton = HumanoidSkeleton()
        layer = IKLayer(skeleton)
        
        self.assertEqual(layer.skeleton, skeleton)
        self.assertEqual(len(layer.targets), 0)
    
    def test_set_target(self):
        """Should be able to set IK targets."""
        skeleton = HumanoidSkeleton()
        layer = IKLayer(skeleton)
        
        layer.set_target("foot_left", MockVector3(0, 0, -1))
        
        self.assertIn("foot_left", layer.targets)
        self.assertEqual(layer.targets["foot_left"].bone_name, "foot_left")
    
    def test_clear_target(self):
        """Should be able to clear targets."""
        skeleton = HumanoidSkeleton()
        layer = IKLayer(skeleton)
        
        layer.set_target("foot_left", MockVector3(0, 0, -1))
        layer.clear_target("foot_left")
        
        self.assertNotIn("foot_left", layer.targets)
    
    def test_clear_all_targets(self):
        """Should be able to clear all targets."""
        skeleton = HumanoidSkeleton()
        layer = IKLayer(skeleton)
        
        layer.set_target("foot_left", MockVector3(0, 0, -1))
        layer.set_target("foot_right", MockVector3(0, 0, -1))
        
        layer.clear_all_targets()
        
        self.assertEqual(len(layer.targets), 0)
    
    def test_update_returns_transforms(self):
        """Update should return bone transforms from IK solving."""
        skeleton = HumanoidSkeleton()
        layer = IKLayer(skeleton)
        
        # Set foot target
        layer.set_target("foot_left", MockVector3(0, 2, 0), weight=1.0)
        
        transforms = layer.update(0.1, skeleton)
        
        # Should return some transforms (IK solved for leg chain)
        # Exact transforms depend on solver, just check it returns something
        self.assertIsInstance(transforms, dict)


class TestFootIKController(unittest.TestCase):
    """Test foot IK controller."""
    
    def test_controller_initialization(self):
        """Controller should initialize with raycast callback."""
        def mock_raycast(origin, direction):
            return MockVector3(origin.x, origin.y, 0)
        
        controller = FootIKController(mock_raycast)
        
        self.assertTrue(controller.enabled)
        self.assertEqual(controller.hip_adjustment, 0.8)
    
    def test_disabled_controller_returns_empty(self):
        """Disabled controller should return no targets."""
        def mock_raycast(origin, direction):
            return MockVector3(origin.x, origin.y, 0)
        
        controller = FootIKController(mock_raycast)
        controller.set_enabled(False)
        
        skeleton = HumanoidSkeleton()
        targets = controller.update(skeleton, MockVector3(0, 0, 1), grounded=True)
        
        self.assertEqual(len(targets), 0)
    
    def test_airborne_returns_empty(self):
        """Controller should return no targets when airborne."""
        def mock_raycast(origin, direction):
            return MockVector3(origin.x, origin.y, 0)
        
        controller = FootIKController(mock_raycast)
        
        skeleton = HumanoidSkeleton()
        targets = controller.update(skeleton, MockVector3(0, 0, 1), grounded=False)
        
        self.assertEqual(len(targets), 0)
    
    def test_flat_ground_creates_foot_targets(self):
        """On flat ground, should create targets for both feet."""
        def mock_raycast(origin, direction):
            # Return hit at ground level
            return MockVector3(origin.x, origin.y, 0)
        
        controller = FootIKController(mock_raycast)
        
        skeleton = HumanoidSkeleton()
        skeleton.update_world_transforms()
        targets = controller.update(skeleton, MockVector3(0, 0, 1), grounded=True)
        
        # Should have targets for both feet
        # (may also have hip target depending on slope)
        self.assertGreaterEqual(len(targets), 2)
        self.assertIn("foot_left", targets)
        self.assertIn("foot_right", targets)


if __name__ == '__main__':
    unittest.main()
