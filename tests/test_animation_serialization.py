"""Tests for animation JSON serialization.

Verifies that animation clips can be serialized to and from JSON
without data loss.
"""

import pytest
from panda3d.core import LVector3f

from engine.animation.core import Transform, Keyframe, AnimationEvent, AnimationClip
from engine.animation.combat import HitWindow, CombatClip


class TestTransformSerialization:
    """Test Transform to_dict/from_dict roundtrip."""
    
    def test_transform_to_dict(self):
        """Test Transform serialization to dict."""
        transform = Transform(
            position=LVector3f(1.0, 2.0, 3.0),
            rotation=LVector3f(45.0, 90.0, 180.0),
            scale=LVector3f(2.0, 2.0, 2.0)
        )
        
        data = transform.to_dict()
        
        assert data['position'] == [1.0, 2.0, 3.0]
        assert data['rotation'] == [45.0, 90.0, 180.0]
        assert data['scale'] == [2.0, 2.0, 2.0]
        
    def test_transform_from_dict(self):
        """Test Transform deserialization from dict."""
        data = {
            'position': [1.0, 2.0, 3.0],
            'rotation': [45.0, 90.0, 180.0],
            'scale': [2.0, 2.0, 2.0]
        }
        
        transform = Transform.from_dict(data)
        
        assert transform.position.x == 1.0
        assert transform.position.y == 2.0
        assert transform.position.z == 3.0
        assert transform.rotation.x == 45.0
        assert transform.scale.x == 2.0
        
    def test_transform_roundtrip(self):
        """Test Transform serialization roundtrip."""
        original = Transform(
            position=LVector3f(1.5, 2.5, 3.5),
            rotation=LVector3f(30.0, 60.0, 90.0),
            scale=LVector3f(1.5, 1.5, 1.5)
        )
        
        data = original.to_dict()
        restored = Transform.from_dict(data)
        
        assert restored.position.x == pytest.approx(original.position.x)
        assert restored.rotation.y == pytest.approx(original.rotation.y)
        assert restored.scale.z == pytest.approx(original.scale.z)


class TestKeyframeSerialization:
    """Test Keyframe to_dict/from_dict roundtrip."""
    
    def test_keyframe_to_dict(self):
        """Test Keyframe serialization."""
        keyframe = Keyframe(
            time=0.5,
            transforms={
                'bone1': Transform(position=LVector3f(1, 0, 0)),
                'bone2': Transform(rotation=LVector3f(45, 0, 0))
            }
        )
        
        data = keyframe.to_dict()
        
        assert data['time'] == 0.5
        assert 'bone1' in data['transforms']
        assert 'bone2' in data['transforms']
        
    def test_keyframe_roundtrip(self):
        """Test Keyframe serialization roundtrip."""
        original = Keyframe(
            time=1.25,
            transforms={
                'arm': Transform(rotation=LVector3f(90, 0, 0)),
                'leg': Transform(position=LVector3f(0, 0, 1))
            }
        )
        
        data = original.to_dict()
        restored = Keyframe.from_dict(data)
        
        assert restored.time == original.time
        assert 'arm' in restored.transforms
        assert restored.transforms['arm'].rotation.x == pytest.approx(90.0)


class TestAnimationEventSerialization:
    """Test AnimationEvent to_dict/from_dict roundtrip."""
    
    def test_event_to_dict(self):
        """Test AnimationEvent serialization."""
        event = AnimationEvent(
            time=0.15,
            event_name='hit_start',
            data={'damage': 10}
        )
        
        data = event.to_dict()
        
        assert data['time'] == 0.15
        assert data['event_name'] == 'hit_start'
        assert data['data']['damage'] == 10
        
    def test_event_roundtrip(self):
        """Test AnimationEvent serialization roundtrip."""
        original = AnimationEvent(
            time=0.25,
            event_name='impact',
            data={'type': 'sword', 'multiplier': 1.5}
        )
        
        data = original.to_dict()
        restored = AnimationEvent.from_dict(data)
        
        assert restored.time == original.time
        assert restored.event_name == original.event_name
        assert restored.data['multiplier'] == 1.5


class TestAnimationClipSerialization:
    """Test AnimationClip to_dict/from_dict roundtrip."""
    
    def test_clip_to_dict(self):
        """Test AnimationClip serialization."""
        clip = AnimationClip(
            name='test_walk',
            duration=1.0,
            looping=True,
            keyframes=[
                Keyframe(time=0.0, transforms={'root': Transform()}),
                Keyframe(time=0.5, transforms={'root': Transform(position=LVector3f(1, 0, 0))})
            ],
            events=[
                AnimationEvent(time=0.25, event_name='footstep', data={})
            ]
        )
        
        data = clip.to_dict()
        
        assert data['name'] == 'test_walk'
        assert data['duration'] == 1.0
        assert data['looping'] is True
        assert len(data['keyframes']) == 2
        assert len(data['events']) == 1
        
    def test_clip_roundtrip(self):
        """Test AnimationClip serialization roundtrip."""
        original = AnimationClip(
            name='attack',
            duration=0.5,
            looping=False,
            keyframes=[
                Keyframe(time=0.0, transforms={'arm': Transform(rotation=LVector3f(0, -90, 0))}),
                Keyframe(time=0.25, transforms={'arm': Transform(rotation=LVector3f(0, 90, 0))})
            ],
            events=[
                AnimationEvent(time=0.15, event_name='hit', data={'damage': 20})
            ]
        )
        
        data = original.to_dict()
        restored = AnimationClip.from_dict(data)
        
        assert restored.name == original.name
        assert restored.duration == original.duration
        assert restored.looping == original.looping
        assert len(restored.keyframes) == len(original.keyframes)
        assert len(restored.events) == len(original.events)
        assert restored.events[0].event_name == 'hit'


class TestHitWindowSerialization:
    """Test HitWindow to_dict/from_dict roundtrip."""
    
    def test_hitwindow_to_dict(self):
        """Test HitWindow serialization."""
        window = HitWindow(
            start_time=0.12,
            end_time=0.18,
            damage_multiplier=1.5
        )
        
        data = window.to_dict()
        
        assert data['start_time'] == 0.12
        assert data['end_time'] == 0.18
        assert data['damage_multiplier'] == 1.5
        
    def test_hitwindow_roundtrip(self):
        """Test HitWindow serialization roundtrip."""
        original = HitWindow(
            start_time=0.1,
            end_time=0.2,
            damage_multiplier=2.0
        )
        
        data = original.to_dict()
        restored = HitWindow.from_dict(data)
        
        assert restored.start_time == original.start_time
        assert restored.end_time == original.end_time
        assert restored.damage_multiplier == original.damage_multiplier


class TestCombatClipSerialization:
    """Test CombatClip to_dict/from_dict roundtrip."""
    
    def test_combat_clip_to_dict(self):
        """Test CombatClip metadata serialization."""
        clip = CombatClip(
            name='slash',
            duration=0.5,
            keyframes=[],
            looping=False,
            hit_windows=[HitWindow(0.12, 0.18, 1.0)],
            can_cancel_after=0.35,
            momentum_influence=0.4,
            recovery_time=0.15
        )
        
        data = clip.to_dict()
        
        assert len(data['hit_windows']) == 1
        assert data['can_cancel_after'] == 0.35
        assert data['momentum_influence'] == 0.4
        assert data['recovery_time'] == 0.15
        
    def test_combat_clip_roundtrip(self):
        """Test CombatClip serialization roundtrip."""
        original = CombatClip(
            name='heavy_attack',
            duration=1.0,
            keyframes=[],
            looping=False,
            hit_windows=[
                HitWindow(0.3, 0.4, 1.5),
                HitWindow(0.6, 0.7, 2.0)
            ],
            can_cancel_after=0.8,
            momentum_influence=0.5,
            recovery_time=0.2
        )
        
        # Serialize combat metadata
        combat_data = original.to_dict()
        
        # Create base clip
        base_clip = AnimationClip(
            name=original.name,
            duration=original.duration,
            keyframes=original.keyframes,
            looping=original.looping,
            events=original.events
        )
        
        # Restore from metadata
        restored = CombatClip.from_dict_metadata(base_clip, combat_data)
        
        assert len(restored.hit_windows) == 2
        assert restored.hit_windows[0].damage_multiplier == 1.5
        assert restored.can_cancel_after == 0.8
        assert restored.momentum_influence == 0.5
