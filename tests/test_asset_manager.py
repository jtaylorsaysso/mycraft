import os
import pytest
from panda3d.core import NodePath
from engine.assets.manager import AssetManager
from engine.animation.voxel_avatar import VoxelAvatar
from engine.animation.core import AnimationClip

def test_asset_manager_avatar_io(tmp_path):
    """Test avatar save/load."""
    # Convert Path object to string for AssetManager
    manager = AssetManager(str(tmp_path))
    
    # Create dummy avatar
    root = NodePath("root")
    # Note: validate=False because mocks/environment might check bones
    avatar = VoxelAvatar(root, validate=False)
    avatar.body_color = (0.5, 0.5, 0.5, 1.0)
    
    # Save
    manager.save_avatar(avatar, "test_hero")
    
    # Verify file exists
    expected_path = tmp_path / "test_hero.mca"
    assert expected_path.exists()
    
    # Load
    loaded = manager.load_avatar("test_hero", root)
    assert loaded.body_color == (0.5, 0.5, 0.5, 1.0)
    assert loaded.skeleton is not None
    
    avatar.cleanup()
    loaded.cleanup()
    
def test_asset_manager_clip_io(tmp_path):
    """Test animation clip save/load."""
    manager = AssetManager(str(tmp_path))
    clip = AnimationClip("walk", 1.0, [])
    
    manager.save_animation_clip(clip, "walk_anim")
    
    expected_path = tmp_path / "walk_anim.mcc"
    assert expected_path.exists()
    
    loaded = manager.load_animation_clip("walk_anim")
    assert loaded.name == "walk"
    assert loaded.duration == 1.0
