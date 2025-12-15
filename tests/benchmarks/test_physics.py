
import pytest
from engine.physics import KinematicState, apply_gravity, integrate_movement
from unittest.mock import MagicMock

class FakeEntity:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.position = MagicMock()
        self.intersects = MagicMock(return_value=MagicMock(hit=False))

def test_physics_update_benchmark(benchmark):
    """Benchmark a single physics update step."""
    
    # Setup
    state = KinematicState()
    entity = FakeEntity()
    
    def ground_check(e):
        return 0.0
    
    def run_update():
        # Update with small dt
        apply_gravity(state, dt=0.016)
        integrate_movement(
            entity, 
            state, 
            dt=0.016, 
            ground_check=ground_check
        )
        
    benchmark(run_update)

def test_gravity_integration_benchmark(benchmark):
    """Benchmark gravity calculation."""
    state = KinematicState()
    state.velocity_y = 10.0
    
    def run_gravity():
        apply_gravity(state, 0.016)
        
    benchmark(run_gravity)
