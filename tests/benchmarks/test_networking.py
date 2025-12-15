
import pytest
import json
import time

def test_message_serialization_benchmark(benchmark):
    """Benchmark JSON serialization of game state snapshots."""
    
    # Create a dummy snapshot with 16 players
    snapshot = {
        "type": "state_snapshot",
        "timestamp": 123456789.0,
        "players": {
            f"player_{i}": {
                "pos": [i*10.0, 5.0, i*10.0],
                "rot_y": 45.0,
                "name": f"Player {i}"
            } for i in range(16)
        }
    }
    
    def serialize():
        json.dumps(snapshot)
        
    benchmark(serialize)

def test_message_deserialization_benchmark(benchmark):
    """Benchmark JSON deserialization."""
    
    snapshot = {
        "type": "state_snapshot",
        "timestamp": 123456789.0,
        "players": {
            f"player_{i}": {
                "pos": [i*10.0, 5.0, i*10.0],
                "rot_y": 45.0,
                "name": f"Player {i}"
            } for i in range(16)
        }
    }
    data = json.dumps(snapshot)
    
    def deserialize():
        json.loads(data)
        
    benchmark(deserialize)
