import sys
import os
import math

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.physics import KinematicState, integrate_movement
from dataclasses import dataclass

@dataclass
class MockEntity:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    @property
    def world_position(self):
        # Mock Ursina Vec3 if needed, or just return tuple/object
        class Vec3Mock:
            def __init__(self, x, y, z): self.x, self.y, self.z = x, y, z
            def __add__(self, other): return Vec3Mock(self.x+other.x, self.y+other.y, self.z+other.z)
        return Vec3Mock(self.x, self.y, self.z)

def test_momentum():
    print("Testing Momentum Integration...")
    state = KinematicState()
    state.velocity_x = 10.0 # Moving right
    
    entity = MockEntity()
    dt = 0.1
    
    # Mock checks
    ground_check = lambda e: 0.0
    wall_check = lambda e, m: False # No walls
    
    integrate_movement(entity, state, dt, ground_check, wall_check)
    
    expected_x = 1.0 # 10 * 0.1
    print(f"Entity X: {entity.x} (Expected {expected_x})")
    assert abs(entity.x - expected_x) < 0.001
    print("Momentum Test Passed")

def test_wall_collision():
    print("\nTesting Wall Collision...")
    state = KinematicState()
    state.velocity_x = 10.0
    
    entity = MockEntity()
    dt = 0.1
    
    # Mock checks
    ground_check = lambda e: 0.0
    # Wall check always returns True (hit wall)
    wall_check = lambda e, m: True 
    
    integrate_movement(entity, state, dt, ground_check, wall_check)
    
    print(f"Entity X: {entity.x} (Expected 0.0 - blocked)")
    print(f"Velocity X: {state.velocity_x} (Expected 0.0 - stopped)")
    
    assert entity.x == 0.0
    assert state.velocity_x == 0.0
    print("Wall Collision Test Passed")

if __name__ == "__main__":
    test_momentum()
    test_wall_collision()
