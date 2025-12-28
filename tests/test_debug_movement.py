"""Debug script for testing movement with the composition-based PlayerControlSystem."""

import sys
import os
import math
from unittest.mock import MagicMock
sys.path.append(os.getcwd())

from panda3d.core import LVector3f, CollisionTraverser, CollisionHandlerQueue
from engine.physics.kinematic import KinematicState
from engine.systems.player_controller import PlayerControlSystem
from engine.components.core import Transform

# Mock World and Components
class MockWorld:
    def __init__(self):
        self.components = {}
        self.entities = {}
        self._systems = []
        self.collision_traverser = CollisionTraverser()

    def get_component(self, entity_id, component_type):
        return self.components.get((entity_id, component_type))
    
    def get_entity_by_tag(self, tag):
        return self.entities.get(tag)
        
    def get_system_by_type(self, name):
        return None  # No other systems for isolation


def test_run_debug():
    """Debug test for PlayerControlSystem with mechanics."""
    print("--- Starting Movement Debug ---")
    
    # Setup
    world = MockWorld()
    base = MagicMock()
    base.cam.getH.return_value = 0.0  # Facing Y+
    base.render = MagicMock()  # Mock render node
    base.camLens = MagicMock()  # Mock camera lens for FOV
    event_bus = MagicMock()
    
    # Create system (composition-based)
    system = PlayerControlSystem(world, event_bus, base)
    
    # Mock config_manager to return sensible defaults
    base.config_manager = MagicMock()
    base.config_manager.get = lambda key, default=None: {
        'mouse_sensitivity': 40.0,
        'fov': 90.0,
        'camera_distance': 4.0,
        'movement_speed': 7.0,
        'gravity': -20.0,
        'god_mode': False,
        'debug_overlay': False,
    }.get(key, default)
    
    # Initialize mechanics (this sets up InputMechanic, etc.)
    system.initialize()
    
    # Setup Player
    player_id = "player_1"
    world.entities["player"] = player_id
    transform = Transform(position=LVector3f(0, 0, 10))  # Start high up
    world.components[(player_id, Transform)] = transform
    
    # Add KinematicState component (now required as component, not dict)
    state = KinematicState()
    world.components[(player_id, KinematicState)] = state
    
    # Store base on world for mechanics access
    world.base = base
    
    # Call on_ready (sets up cameras, initializes mechanics)
    system.on_ready()
    
    # Run initial update to populate physics state
    system.update(0.0)
    
    # Access physics state from component (not system.physics_states)
    print(f"Initial Pos: {transform.position}")
    print(f"Initial Vel: {state.velocity_x}, {state.velocity_y}, {state.velocity_z}")
    
    # Find the InputMechanic to simulate key presses
    input_mechanic = None
    for mech in system.mechanics:
        if mech.__class__.__name__ == 'InputMechanic':
            input_mechanic = mech
            break
    
    if input_mechanic and input_mechanic.input_manager:
        # Test 1: Simulate 'W' press (Forward/Y+)
        print("\n--- Simulating 'W' Forward Movement ---")
        input_mechanic.input_manager.keys_down.add('w')
        
        dt = 0.016
        for i in range(10):
            system.update(dt)
            print(f"Frame {i+1}: Pos={transform.position}, Vel=({state.velocity_x:.3f}, {state.velocity_y:.3f}, {state.velocity_z:.3f})")
        
        input_mechanic.input_manager.keys_down.discard('w')
        
        # Test 2: Gravity only
        print("\n--- Gravity Fall ---")
        for i in range(10):
            system.update(dt)
            print(f"Frame {i+1}: Pos={transform.position}, Vel=({state.velocity_x:.3f}, {state.velocity_y:.3f}, {state.velocity_z:.3f})")
    else:
        print("Could not find InputMechanic with input_manager")


if __name__ == '__main__':
    test_run_debug()
