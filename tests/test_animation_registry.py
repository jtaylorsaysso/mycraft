"""Tests for AnimationRegistry.

Verifies clip registration, retrieval, and JSON save/load functionality.
"""

import pytest
from pathlib import Path
import tempfile
import json

from panda3d.core import LVector3f

from engine.animation.animation_registry import AnimationRegistry
from engine.animation.core import AnimationClip, Keyframe, Transform, AnimationEvent
from engine.animation.combat import CombatClip, HitWindow


class TestAnimationRegistry:
    """Test AnimationRegistry functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = AnimationRegistry()
        
        # Create test clip
        self.test_clip = AnimationClip(
            name='test_walk',
            duration=1.0,
            looping=True,
            keyframes=[
                Keyframe(time=0.0, transforms={'root': Transform()}),
                Keyframe(time=0.5, transforms={'root': Transform(position=LVector3f(1, 0, 0))})
            ]
        )
        
        # Create test combat clip
        self.test_combat_clip = CombatClip(
            name='test_slash',
            duration=0.5,
            looping=False,
            keyframes=[
                Keyframe(time=0.0, transforms={'arm': Transform()}),
                Keyframe(time=0.25, transforms={'arm': Transform(rotation=LVector3f(0, 90, 0))})
            ],
            hit_windows=[HitWindow(0.12, 0.18, 1.0)],
            can_cancel_after=0.35
        )
        
    def test_register_clip(self):
        """Test registering a clip."""
        self.registry.register_clip(self.test_clip)
        
        assert 'test_walk' in self.registry.list_clips()
        
    def test_register_combat_clip(self):
        """Test registering a combat clip."""
        self.registry.register_combat_clip(self.test_combat_clip)
        
        assert 'test_slash' in self.registry.list_clips()
        assert 'test_slash' in self.registry.list_combat_clips()
        
    def test_get_clip(self):
        """Test retrieving a clip."""
        self.registry.register_clip(self.test_clip)
        
        retrieved = self.registry.get_clip('test_walk')
        
        assert retrieved is not None
        assert retrieved.name == 'test_walk'
        assert retrieved.duration == 1.0
        
    def test_get_combat_clip(self):
        """Test retrieving a combat clip."""
        self.registry.register_combat_clip(self.test_combat_clip)
        
        retrieved = self.registry.get_combat_clip('test_slash')
        
        assert retrieved is not None
        assert isinstance(retrieved, CombatClip)
        assert len(retrieved.hit_windows) == 1
        
    def test_get_nonexistent_clip(self):
        """Test retrieving a clip that doesn't exist."""
        retrieved = self.registry.get_clip('nonexistent')
        
        assert retrieved is None
        
    def test_list_clips(self):
        """Test listing all clips."""
        self.registry.register_clip(self.test_clip)
        self.registry.register_combat_clip(self.test_combat_clip)
        
        clips = self.registry.list_clips()
        
        assert len(clips) == 2
        assert 'test_walk' in clips
        assert 'test_slash' in clips
        
    def test_save_to_json(self):
        """Test saving a clip to JSON."""
        self.registry.register_clip(self.test_clip)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_walk.json'
            self.registry.save_to_json('test_walk', output_path)
            
            assert output_path.exists()
            
            # Verify JSON content
            with open(output_path, 'r') as f:
                data = json.load(f)
                
            assert data['name'] == 'test_walk'
            assert data['duration'] == 1.0
            assert data['looping'] is True
            
    def test_save_combat_clip_to_json(self):
        """Test saving a combat clip with metadata to JSON."""
        self.registry.register_combat_clip(self.test_combat_clip)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_slash.json'
            self.registry.save_to_json('test_slash', output_path)
            
            assert output_path.exists()
            
            # Verify JSON content includes combat metadata
            with open(output_path, 'r') as f:
                data = json.load(f)
                
            assert 'combat_metadata' in data
            assert len(data['combat_metadata']['hit_windows']) == 1
            assert data['combat_metadata']['can_cancel_after'] == 0.35
            
    def test_load_from_json(self):
        """Test loading a clip from JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save first
            self.registry.register_clip(self.test_clip)
            json_path = Path(tmpdir) / 'test_walk.json'
            self.registry.save_to_json('test_walk', json_path)
            
            # Load into new registry
            new_registry = AnimationRegistry()
            loaded_clip = new_registry.load_from_json(json_path)
            
            assert loaded_clip.name == 'test_walk'
            assert loaded_clip.duration == 1.0
            assert loaded_clip.looping is True
            assert len(loaded_clip.keyframes) == 2
            
    def test_reload_from_json(self):
        """Test reloading a clip from JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save clip
            self.registry.register_clip(self.test_clip)
            json_path = Path(tmpdir) / 'test_walk.json'
            self.registry.save_to_json('test_walk', json_path)
            
            # Modify registry
            self.registry.clips.clear()
            assert len(self.registry.list_clips()) == 0
            
            # Reload
            self.registry.reload_from_json(json_path)
            
            assert 'test_walk' in self.registry.list_clips()
            
    def test_scan_directory(self):
        """Test scanning directory for JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create subdirectory structure
            combat_dir = tmpdir / 'combat'
            combat_dir.mkdir()
            
            # Save clips
            self.registry.register_clip(self.test_clip)
            self.registry.register_combat_clip(self.test_combat_clip)
            
            self.registry.save_to_json('test_walk', tmpdir / 'test_walk.json')
            self.registry.save_to_json('test_slash', combat_dir / 'test_slash.json')
            
            # Clear and scan
            new_registry = AnimationRegistry()
            new_registry.scan_directory(tmpdir)
            
            assert 'test_walk' in new_registry.list_clips()
            assert 'test_slash' in new_registry.list_clips()
            
    def test_save_nonexistent_clip_raises_error(self):
        """Test that saving a nonexistent clip raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'nonexistent.json'
            
            with pytest.raises(ValueError, match="not found"):
                self.registry.save_to_json('nonexistent', output_path)
