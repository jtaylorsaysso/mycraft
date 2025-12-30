"""Verification test for Animation Events System."""
import sys
from unittest.mock import MagicMock, patch

# 1. Setup global mocks BEFORE importing engine modules
class StubVec3:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = float(x), float(y), float(z)
    def __add__(self, other):
        return StubVec3(self.x + other.x, self.y + other.y, self.z + other.z)
    def __sub__(self, other):
        return StubVec3(self.x - other.x, self.y - other.y, self.z - other.z)
    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return StubVec3(self.x * other, self.y * other, self.z * other)
        return StubVec3(0,0,0) # Simplified
    def length(self): return 0.0

class StubVec4:
    def __init__(self, x=0, y=0, z=0, w=0):
        self.x, self.y, self.z, self.w = float(x), float(y), float(z), float(w)

class StubNodePath:
    def __init__(self, name="mock"): pass
    def attachNewNode(self, name): return StubNodePath(name)
    def setPos(self, *args): pass
    def setHpr(self, *args): pass
    def setScale(self, *args): pass

mock_panda = MagicMock()
mock_panda.LVector3f = StubVec3
mock_panda.LVector4f = StubVec4
mock_panda.NodePath = StubNodePath
mock_panda.CardMaker = MagicMock()
mock_panda.TransparencyAttrib = MagicMock()

# Patch sys.modules
sys.modules["panda3d"] = MagicMock()
sys.modules["panda3d.core"] = mock_panda

# Patch direct modules (Panda3D Python component)
sys.modules["direct"] = MagicMock()
sys.modules["direct.interval"] = MagicMock()
sys.modules["direct.interval.IntervalGlobal"] = MagicMock()
sys.modules["direct.showbase"] = MagicMock()
sys.modules["direct.showbase.ShowBase"] = MagicMock()

import unittest

# Mock dependencies
class MockSkeleton:
    def get_bone(self, name):
        bone = MagicMock()
        bone.rest_transform.position = StubVec3(0, 0, 0)
        bone.rest_transform.rotation = StubVec3(0, 0, 0)
        return bone

class TestAnimationEvents(unittest.TestCase):
    def test_sword_slash_events(self):
        """Test that sword slash triggers events at correct times."""
        # Now we can import engine modules safely (they will use the mocks in sys.modules)
        from engine.player_mechanics.combat_animation_source import CombatAnimationSource
        
        source = CombatAnimationSource()
        skeleton = MockSkeleton()
        
        # Track events
        events_fired = []
        def on_hit_start(data): events_fired.append(("start", data))
        def on_impact(data): events_fired.append(("impact", data))
        def on_hit_end(data): events_fired.append(("end", data))
        
        # Register callbacks
        source.register_event_callback("attack_hit_start", on_hit_start)
        source.register_event_callback("attack_impact", on_impact)
        source.register_event_callback("attack_hit_end", on_hit_end)
        
        # Play animation
        source.play("sword_slash")
        
        # Step 1: t=0.0 -> t=0.1 (No events yet, start is at 0.12)
        source.update(0.1, skeleton)
        self.assertEqual(len(events_fired), 0)
        
        # Step 2: t=0.1 -> t=0.13 (Crosses 0.12)
        source.update(0.03, skeleton) # total 0.13
        self.assertEqual(len(events_fired), 1)
        self.assertEqual(events_fired[0][0], "start")
        
        # Step 3: t=0.13 -> t=0.16 (Crosses 0.15 impact)
        source.update(0.03, skeleton) # total 0.16
        self.assertEqual(len(events_fired), 2)
        self.assertEqual(events_fired[1][0], "impact")
        self.assertEqual(events_fired[1][1]["type"], "sword_slash")
        
        # Step 4: t=0.16 -> t=0.20 (Crosses 0.18 end)
        source.update(0.04, skeleton) # total 0.20
        self.assertEqual(len(events_fired), 3)
        self.assertEqual(events_fired[2][0], "end")

if __name__ == '__main__':
    unittest.main()
