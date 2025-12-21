"""
DEPRECATED: Tests for Ursina-based RemotePlayer.

These tests use the deprecated games.voxel_world.entities.remote_player.RemotePlayer.
New tests should target engine.networking.remote_player.RemotePlayer.

Kept for reference during migration.
"""

import unittest
import sys
from unittest.mock import MagicMock, patch
import time

# Mock ursina before importing remote_player
mock_ursina = MagicMock()
sys.modules['ursina'] = mock_ursina
# Mock specific components used in RemotePlayer
class MockEntity:
    def __init__(self, **kwargs):
        self.position = MockVec3(0,0,0)
        self.rotation_y = 0.0
        for k, v in kwargs.items():
            setattr(self, k, v)

mock_ursina.Entity = MockEntity
mock_ursina.color = MagicMock()
mock_ursina.Vec3 = MagicMock
mock_ursina.color = MagicMock()
mock_ursina.Vec3 = MagicMock

# Mock Text to handle background property
def MockText(**kwargs):
    m = MagicMock()
    # If background=True was passed, ensure the attribute is a Mock, not bool
    if kwargs.get('background'):
        m.background = MagicMock()
    return m

mock_ursina.Text = MockText

mock_ursina.lerp = lambda a, b, t: a + (b - a) * t
mock_ursina.time = MagicMock()

# Mock engine.animation
sys.modules['engine.animation'] = MagicMock()

# Now we can safely import RemotePlayer
# But wait, RemotePlayer implementation uses Vec3(*pos). MagicMock(*pos) might fail if it doesn't behave like Vec3.
# Let's verify if we can make a simple Vec3 mock.
class MockVec3:
    def __init__(self, x=0, y=0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    def __add__(self, other):
        return MockVec3(self.x + other.x, self.y + other.y, self.z + other.z)
    def __sub__(self, other):
        return MockVec3(self.x - other.x, self.y - other.y, self.z - other.z)
    def __mul__(self, other):
        return MockVec3(self.x * other, self.y * other, self.z * other)
    def __truediv__(self, other):
        return MockVec3(self.x / other, self.y / other, self.z / other)
    def length(self):
        return (self.x**2 + self.y**2 + self.z**2)**0.5
    def __eq__(self, other):
        if not isinstance(other, MockVec3): return False
        # Approx equality
        return abs(self.x - other.x) < 0.001 and abs(self.y - other.y) < 0.001 and abs(self.z - other.z) < 0.001
    def __repr__(self):
        return f"Vec3({self.x}, {self.y}, {self.z})"

mock_ursina.Vec3 = MockVec3

# We need to reload remote_player if it was already imported, or just import now
from games.voxel_world.entities.remote_player import RemotePlayer
from tests.test_utils.network_simulator import NetworkSimulator

class TestNetworkQuality(unittest.TestCase):
    def setUp(self):
        # Reset RemotePlayer dependencies
        pass

    def test_simulator_packet_loss(self):
        """Verify simulator drops packets approximately as requested."""
        sim = NetworkSimulator(packet_loss_pct=50.0)
        drops = 0
        total = 1000
        for _ in range(total):
            if sim.should_drop_packet():
                drops += 1
        
        # 50% loss +- 10%
        self.assertTrue(400 <= drops <= 600, f"Packet loss {drops}/{total} not within range")

    def test_remote_player_interpolation_smoothness(self):
        """Verify RemotePlayer interpolates smoothly towards target despite jittery updates."""
        player = RemotePlayer()
        player.position = MockVec3(0, 0, 0)
        player.rotation_y = 0
        
        # Simulate moving to (10, 0, 0) over 1 second
        target = MockVec3(10, 0, 0)
        player.set_target((10, 0, 0), 0)
        
        # Step for 0.1s
        mock_ursina.time.dt = 0.1
        player.update()
        
        # Should have moved towards target
        # lerp speed is 10.0. lerp(0, 10, 0.1 * 10) = lerp(0, 10, 1.0) = 10.
        # Wait, lerp_speed 10 means it reaches target in 0.1s?
        # RemotePlayer.lerp_speed = 10.0
        # If dt=0.1, t = 1.0. It snaps instantly.
        # That's very fast interpolation.
        
        # Let's adjust lerp_speed for the test or use smaller dt
        player.lerp_speed = 5.0 # t = 0.5
        player.position = MockVec3(0, 0, 0) # Reset
        
        player.update()
        
        # Expect position to be halfway
        self.assertAlmostEqual(player.position.x, 5.0, delta=0.1)
        
    def test_packet_loss_recovery(self):
        """Verify RemotePlayer eventually reaches target even if updates stop (loss)."""
        player = RemotePlayer()
        player.position = MockVec3(0, 0, 0)
        player.lerp_speed = 2.0
        
        # Final update received
        player.set_target((10, 0, 0), 0)
        
        # Then packet loss happens - no more set_target calls
        # Player should continue interpolating to the last known target
        
        mock_ursina.time.dt = 0.1
        for _ in range(10): # 1 second total
            player.update()
            
        # 1s * 2.0 = 2.0 ? No, lerp implies asymptotic approach usually if using lerp(current, target)
        # Formula: current = current + (target - current) * t
        # It never fully reaches 10.0 mathematically but gets close.
        # If t >= 1 it snaps.
        # With speed 2.0 and dt 0.1, t=0.2. 
        # Update 1: 0 + (10)*0.2 = 2.0
        # Update 2: 2 + (8)*0.2 = 3.6
        # ...
        
        self.assertTrue(player.position.x > 5.0, "Player should approach target without new packets")
        self.assertTrue(player.position.x <= 10.0)

    def test_jittery_updates(self):
        """Verify interp behaves well when updates arrive with irregular timing."""
        player = RemotePlayer()
        player.position = MockVec3(0, 0, 0)
        player.lerp_speed = 5.0
        
        # Target moves 1 unit every 0.1s (speed 10)
        # But updates arrive with jitter: 0.05s, 0.15s, 0.05s...
        
        current_time = 0
        server_pos_x = 0
        
        # Simulate 10 steps
        for i in range(10):
            # Move server object
            server_pos_x += 1.0 # 1.0 unit per step
            
            # Update arrives. Late or early?
            # Let's say we just call set_target with new pos
            player.set_target((server_pos_x, 0, 0), 0)
            
            # Update frame (render)
            dt = 0.1
            if i % 2 == 0:
                dt = 0.05 # Fast frame
            else:
                dt = 0.15 # Slow frame
            
            mock_ursina.time.dt = dt
            player.update()
            
            # Position should be roughly following server_pos_x
            # It lags behind due to lerp.
            diff = abs(player.position.x - server_pos_x)
            # Should not be massive
            self.assertTrue(diff < 2.0, f"Diverged too far: {diff} at step {i}")

if __name__ == '__main__':
    unittest.main()
