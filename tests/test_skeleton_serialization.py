"""Tests for skeleton and avatar serialization."""

import pytest
from panda3d.core import LVector3f, NodePath

from engine.animation.skeleton import (
    Skeleton, HumanoidSkeleton, Bone, BoneConstraints, Socket
)
from engine.animation.voxel_avatar import VoxelAvatar


class TestSkeletonSerialization:
    """Test serialization of skeleton components."""

    def test_bone_constraints_serialization(self):
        """Test BoneConstraints to_dict/from_dict roundtrip."""
        constraints = BoneConstraints(
            min_h=-45, max_h=45,
            min_p=-10, max_p=10,
            min_r=-5, max_r=5
        )
        data = constraints.to_dict()
        
        assert data["min_h"] == -45
        assert data["max_h"] == 45
        
        restored = BoneConstraints.from_dict(data)
        assert restored.min_h == constraints.min_h
        assert restored.max_h == constraints.max_h
        assert restored.min_p == constraints.min_p
        assert restored.max_r == constraints.max_r

    def test_socket_serialization(self):
        """Test Socket to_dict/from_dict roundtrip."""
        socket = Socket(
            name="test_socket",
            parent_bone_name="head",
            offset_position=LVector3f(1, 2, 3),
            offset_rotation=LVector3f(45, 90, 0)
        )
        data = socket.to_dict()
        
        assert data["name"] == "test_socket"
        assert data["parent_bone_name"] == "head"
        assert data["offset_position"] == [1.0, 2.0, 3.0]
        
        restored = Socket.from_dict(data)
        assert restored.name == socket.name
        assert restored.parent_bone_name == socket.parent_bone_name
        assert restored.offset_position.x == socket.offset_position.x
        assert restored.offset_position.y == socket.offset_position.y
        assert restored.offset_position.z == socket.offset_position.z
        
        # Test offset rotation manually too
        assert restored.offset_rotation.x == socket.offset_rotation.x
        assert restored.offset_rotation.y == socket.offset_rotation.y
        assert restored.offset_rotation.z == socket.offset_rotation.z

    def test_bone_serialization(self):
        """Test Bone to_dict/from_dict roundtrip."""
        # Create a small chain
        root = Bone("root", 0.0)
        child = Bone("child", 1.0, parent=root)
        child.local_transform.position = LVector3f(0, 5, 0)
        
        # Serialize root (recursive)
        data = root.to_dict()
        
        assert data["name"] == "root"
        assert len(data["children"]) == 1
        assert data["children"][0]["name"] == "child"
        assert data["children"][0]["local_pos"] == [0.0, 5.0, 0.0]
        
        # Restore
        restored = Bone.from_dict(data)
        assert restored.name == "root"
        assert len(restored.children) == 1
        
        restored_child = restored.children[0]
        assert restored_child.name == "child"
        assert restored_child.parent == restored
        assert restored_child.local_transform.position.y == 5.0

    def test_skeleton_serialization(self):
        """Test full Skeleton serialization."""
        skel = Skeleton("base")
        skel.add_bone("b1", "base", 1.0)
        skel.add_bone("b2", "b1", 0.5)
        skel.add_socket("s1", "b2", offset_position=LVector3f(0, 1, 0))
        
        data = skel.to_dict()
        
        assert data["root_bone"]["name"] == "base"
        assert len(data["sockets"]) == 1
        
        restored = Skeleton.from_dict(data)
        assert "base" in restored.bones
        assert "b1" in restored.bones
        assert "b2" in restored.bones
        assert "s1" in restored.sockets
        
        b2 = restored.get_bone("b2")
        assert b2.parent.name == "b1"
        assert b2.length == 0.5

    def test_humanoid_skeleton_serialization(self):
        """Test HumanoidSkeleton serialization."""
        skel = HumanoidSkeleton()
        # Verify initial state
        assert "head" in skel.bones
        assert "hand_l_socket" in skel.sockets
        
        # Modify it slightly to ensure we persist changes
        skel.get_bone("head").length = 99.0
        
        data = skel.to_dict()
        
        # Restore
        restored = HumanoidSkeleton.from_dict(data)
        
        assert isinstance(restored, HumanoidSkeleton)
        assert "head" in restored.bones
        assert restored.get_bone("head").length == 99.0  # Check modification persisted
        assert "hand_l_socket" in restored.sockets


class TestVoxelAvatarSerialization:
    """Test VoxelAvatar serialization."""
    
    def test_avatar_roundtrip(self):
        """Test full avatar roundtrip."""
        # Need a panda node for avatar
        root = NodePath("test_root")
        
        avatar = VoxelAvatar(root, validate=False)
        avatar.body_color = (1.0, 0.0, 0.0, 1.0)
        
        # Modify skeleton
        avatar.skeleton.add_socket("custom_socket", "head")
        
        data = avatar.to_dict()
        
        assert data["type"] == "avatar"
        assert data["skeleton_type"] == "HumanoidSkeleton"
        assert data["body_color"] == [1.0, 0.0, 0.0, 1.0]
        
        # Restore
        restored = VoxelAvatar.from_dict(data, root)
        
        assert restored.body_color == (1.0, 0.0, 0.0, 1.0)
        assert isinstance(restored.skeleton, HumanoidSkeleton)
        assert "custom_socket" in restored.skeleton.sockets
        
        avatar.cleanup()
        restored.cleanup()
