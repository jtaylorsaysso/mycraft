"""Tests for the ClaimedZone component and related functionality."""

import pytest
from engine.components.claimed_zone import ClaimedZone, CHUNK_SIZE


class TestClaimedZone:
    """Tests for chunk-aligned ClaimedZone component."""
    
    def test_creation(self):
        """Test basic zone creation."""
        zone = ClaimedZone(
            owner_id="player_1",
            chunk_coords=[(0, 0), (1, 0)],
        )
        assert zone.owner_id == "player_1"
        assert len(zone.chunk_coords) == 2
        assert zone.blocks == {}
        assert zone.allowed_editors == []
        
    def test_contains_inside_chunk(self):
        """Test that positions inside zone's chunks return True."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0)])
        
        # Inside chunk (0, 0) - world coords 0-15 for x and z
        assert zone.contains((0, 5, 0))
        assert zone.contains((8, 10, 8))
        assert zone.contains((15, 100, 15))  # Any Y is fine
        
    def test_contains_multiple_chunks(self):
        """Test zone spanning multiple chunks."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0), (1, 0), (0, 1)])
        
        # Chunk (0, 0)
        assert zone.contains((8, 5, 8))
        
        # Chunk (1, 0) - world x=16-31
        assert zone.contains((20, 5, 8))
        
        # Chunk (0, 1) - world z=16-31
        assert zone.contains((8, 5, 20))
        
    def test_contains_outside(self):
        """Test that positions outside zone return False."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0)])
        
        # Outside - chunk (1, 0)
        assert not zone.contains((16, 5, 8))
        
        # Outside - chunk (0, 1)
        assert not zone.contains((8, 5, 16))
        
        # Outside - chunk (-1, 0)
        assert not zone.contains((-1, 5, 8))
        
    def test_can_edit_owner(self):
        """Test owner has edit permission."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0)])
        assert zone.can_edit("p1") is True
        
    def test_can_edit_stranger(self):
        """Test stranger has no permission."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0)])
        assert zone.can_edit("p2") is False
        
    def test_add_editor(self):
        """Test adding allowed editor."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0)])
        
        assert zone.add_editor("p2") is True
        assert zone.can_edit("p2") is True
        
        # Adding again returns False
        assert zone.add_editor("p2") is False
        
    def test_remove_editor(self):
        """Test removing an editor."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0)])
        zone.add_editor("p2")
        
        assert zone.remove_editor("p2") is True
        assert zone.can_edit("p2") is False
        
        # Removing again returns False
        assert zone.remove_editor("p2") is False
        
    def test_add_block_inside(self):
        """Test adding blocks inside zone."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0)])
        
        result = zone.add_block((8, 5, 8), "stone")
        assert result is True
        assert (8, 5, 8) in zone.blocks
        assert zone.blocks[(8, 5, 8)] == "stone"
        
    def test_add_block_outside(self):
        """Test adding blocks outside zone fails."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0)])
        
        result = zone.add_block((100, 5, 100), "stone")
        assert result is False
        assert (100, 5, 100) not in zone.blocks
        
    def test_remove_block(self):
        """Test removing blocks from zone."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0)])
        zone.add_block((1, 1, 1), "stone")
        
        result = zone.remove_block((1, 1, 1))
        assert result is True
        assert (1, 1, 1) not in zone.blocks
        
    def test_remove_nonexistent_block(self):
        """Test removing block that doesn't exist."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0)])
        
        result = zone.remove_block((5, 5, 5))
        assert result is False
        
    def test_get_world_bounds(self):
        """Test world bounds calculation."""
        zone = ClaimedZone(owner_id="p1", chunk_coords=[(0, 0), (1, 1)])
        
        min_pos, max_pos = zone.get_world_bounds()
        assert min_pos == (0, 0)
        assert max_pos == (32, 32)
        
    def test_serialization_roundtrip(self):
        """Test to_dict and from_dict preserve data."""
        original = ClaimedZone(
            owner_id="player_42",
            chunk_coords=[(5, 10), (5, 11)],
            allowed_editors=["friend_1"],
            name="My Base"
        )
        original.add_block((80, 5, 160), "cobblestone")
        original.add_block((81, 6, 161), "wood")
        
        # Serialize
        data = original.to_dict()
        
        # Deserialize
        restored = ClaimedZone.from_dict(data)
        
        assert restored.owner_id == original.owner_id
        assert restored.chunk_coords == original.chunk_coords
        assert restored.allowed_editors == original.allowed_editors
        assert restored.name == original.name
        assert len(restored.blocks) == 2
        assert restored.blocks[(80, 5, 160)] == "cobblestone"
        assert restored.blocks[(81, 6, 161)] == "wood"
