
import pytest
import sys
from unittest.mock import MagicMock

# Mock Panda3D modules before imports
sys.modules['direct'] = MagicMock()
sys.modules['direct.interval'] = MagicMock()
sys.modules['direct.interval.IntervalGlobal'] = MagicMock()
sys.modules['direct.fsm'] = MagicMock()
sys.modules['direct.fsm.FSM'] = MagicMock()
sys.modules['panda3d'] = MagicMock()
sys.modules['panda3d.core'] = MagicMock()

import os
from engine.assets.poi_template import POITemplate
from games.voxel_world.pois.template_poi_generator import TemplatePOIGenerator
from engine.assets.manager import AssetManager

# Mock classes
class MockAssetManager:
    def load_poi_template(self, name):
        return POITemplate(
            name="Test POI",
            poi_type="test",
            blocks=[(0,0,0,"stone"), (1,0,0,"dirt")],
            entities=[{"type": "skeleton", "x": 0, "y": 1, "z": 0}],
            loot_points=[{"x": 0, "y": 1, "z": 0, "items": ["sword"]}]
        )

def test_poi_template_serialization():
    t = POITemplate(
        name="Shrine",
        poi_type="shrine",
        blocks=[(0, 0, 0, "stone")],
        entities=[{"type": "chest", "x": 0, "y": 1, "z": 0}],
        biome_affinity=["forest"]
    )
    
    data = t.to_dict()
    assert data["name"] == "Shrine"
    assert data["blocks"] == [(0, 0, 0, "stone")]
    assert data["biome_affinity"] == ["forest"]
    
    t2 = POITemplate.from_dict(data)
    assert t2.name == t.name
    assert t2.blocks == [(0, 0, 0, "stone")]

def test_poi_template_bounds():
    t = POITemplate(
        name="Bounds Test",
        poi_type="test",
        blocks=[
            (-1, 0, 0, "a"),
            (1, 2, 0, "b"),
            (0, 0, 3, "c")
        ]
    )
    t.calculate_bounds()
    assert t.bounds_min == (-1, 0, 0)
    assert t.bounds_max == (1, 2, 3)

def test_template_generator_offsets(monkeypatch):
    # Mock AssetManager in the generator module
    monkeypatch.setattr("games.voxel_world.pois.template_poi_generator.AssetManager", MockAssetManager)
    
    gen = TemplatePOIGenerator(12345, "test")
    
    # Generate at 10, 20, 10
    poi = gen.generate(10, 20, 10, 12345)
    
    # Check offsets
    # Block original (0,0,0) -> (10, 20, 10)
    assert (10, 20, 10, "stone") in poi.blocks
    # Block original (1,0,0) -> (11, 20, 10)
    assert (11, 20, 10, "dirt") in poi.blocks
    
    # Check entities
    # Entity original (0,1,0) -> (10, 21, 10)
    assert ("skeleton", 10, 21, 10) in poi.entities
    
    # Check loot
    # Loot original (0,1,0) -> (10, 21, 10)
    assert (10, 21, 10) in poi.loot

