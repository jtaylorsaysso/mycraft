
import sys
import os
import math
from unittest.mock import MagicMock
sys.path.append(os.getcwd())

from panda3d.core import LVector3f, CollisionTraverser, CollisionHandlerQueue
from engine.physics.kinematic import KinematicState
from engine.systems.input import PlayerControlSystem
from engine.components.core import Transform

# Mock World and Components
class MockWorld:
    def __init__(self):
        self.components = {}
        self.entities = {}
        self._systems = []

    def get_component(self, entity_id, component_type):
        return self.components.get((entity_id, component_type))
    
    def get_entity_by_tag(self, tag):
        return self.entities.get(tag)
        
    def get_system_by_type(self, name):
        return None  # No other systems for isolation

# Mock Input
class MockInput:
    def __init__(self):
        self.keys = {}
        self.mouse_delta = (0, 0)
        
    def is_key_down(self, key):
        return self.keys.get(key, False)
        
    def update(self): pass
    def lock_mouse(self): pass

# Run Test
def test_run_debug():
    print("--- Starting Movement Debug ---")
    
    # Setup
    world = MockWorld()
    base = MagicMock()
    base.cam.getH.return_value = 0.0  # Facing Y+
    base.render = MagicMock() # Mock render node
    event_bus = MagicMock()
    input_mgr = MockInput()
    
    # Correct signature: world, event_bus, base
    system = PlayerControlSystem(world, event_bus, base)
    
    # Manually inject input manager (usually created in initialize)
    system.input = input_mgr
    
    system.collision_traverser = CollisionTraverser() # Use real traverser (empty)
    
    # Configure CollisionHandlerQueue mock if it's a mock
    # This handles the case where Panda3D is mocked globally in conftest.py
    if isinstance(CollisionHandlerQueue, MagicMock) or hasattr(CollisionHandlerQueue, 'return_value'):
        # Configure any new instance created to return 0 hits by default
        CollisionHandlerQueue.return_value.getNumEntries.return_value = 0
    
    # Setup Player
    player_id = "player_1"
    world.entities["player"] = player_id
    transform = Transform(position=LVector3f(0, 0, 10)) # Start high up
    world.components[(player_id, Transform)] = transform
    
    # Init System
    system.on_ready()
    
    # Run one update to initialize physics state
    system.update(0.0)
    
    # Access State
    state = system.physics_states[player_id]
    print(f"Initial Pos: {transform.position}")
    print(f"Initial Vel: {state.velocity_x}, {state.velocity_y}, {state.velocity_z}")
    
    # Test 1: Press 'W' (Forward/Y+)
    print("\n--- Pressing 'W' (Forward) ---")
    input_mgr.keys['w'] = True
    
    dt = 0.016
    for i in range(10):
        system.update(dt)
        print(f"Frame {i+1}: Pos={transform.position}, Vel=({state.velocity_x:.3f}, {state.velocity_y:.3f}, {state.velocity_z:.3f})")
        
    input_mgr.keys['w'] = False
    
    # Test 2: Gravity only
    print("\n--- Gravity Fall ---")
    for i in range(10):
        system.update(dt)
        print(f"Frame {i+1}: Pos={transform.position}, Vel=({state.velocity_x:.3f}, {state.velocity_y:.3f}, {state.velocity_z:.3f})")
