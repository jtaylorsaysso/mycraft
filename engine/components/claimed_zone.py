"""ClaimedZone component for player-owned build zones.

This component marks entities as player-claimed areas where
blocks can be placed/removed during gameplay. Zones are aligned
to chunk boundaries (16x16 blocks) for efficient networking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set

# Chunk size constant (matches ChunkManager)
CHUNK_SIZE = 16


@dataclass
class ClaimedZone:
    """ECS component marking a player-claimed build zone.
    
    Zones are chunk-aligned for efficient networking and collision.
    Each zone can span one or more chunks.
    
    Attributes:
        owner_id: Entity ID of the player who owns this zone
        chunk_coords: List of (chunk_x, chunk_z) tuples defining the zone
        allowed_editors: Player IDs who can edit (in addition to owner)
        blocks: Dict mapping positions to block types for tracking edits
        name: Optional display name for the zone
    """
    owner_id: str
    chunk_coords: List[Tuple[int, int]] = field(default_factory=list)
    allowed_editors: List[str] = field(default_factory=list)
    blocks: Dict[Tuple[int, int, int], str] = field(default_factory=dict)
    name: str = "Build Zone"
    
    def contains(self, pos: Tuple[int, int, int]) -> bool:
        """Check if a world position is within this zone.
        
        Args:
            pos: World position (x, y, z) to check
            
        Returns:
            True if position's chunk is in this zone
        """
        chunk_x = pos[0] // CHUNK_SIZE
        chunk_z = pos[2] // CHUNK_SIZE  # Z is horizontal in Panda3D
        return (chunk_x, chunk_z) in self.chunk_coords
    
    def can_edit(self, player_id: str) -> bool:
        """Check if a player has edit permission.
        
        Args:
            player_id: ID of player to check
            
        Returns:
            True if player is owner or in allowed_editors
        """
        return player_id == self.owner_id or player_id in self.allowed_editors
    
    def add_editor(self, player_id: str) -> bool:
        """Add a player to allowed editors.
        
        Args:
            player_id: ID of player to add
            
        Returns:
            True if added, False if already present
        """
        if player_id not in self.allowed_editors and player_id != self.owner_id:
            self.allowed_editors.append(player_id)
            return True
        return False
    
    def remove_editor(self, player_id: str) -> bool:
        """Remove a player from allowed editors.
        
        Args:
            player_id: ID of player to remove
            
        Returns:
            True if removed, False if not found
        """
        if player_id in self.allowed_editors:
            self.allowed_editors.remove(player_id)
            return True
        return False
        
    def add_block(self, pos: Tuple[int, int, int], block_type: str) -> bool:
        """Record a block placement in this zone.
        
        Args:
            pos: Block position
            block_type: Type of block placed
            
        Returns:
            True if position is in zone and block was added
        """
        if not self.contains(pos):
            return False
        self.blocks[pos] = block_type
        return True
        
    def remove_block(self, pos: Tuple[int, int, int]) -> bool:
        """Record a block removal in this zone.
        
        Args:
            pos: Block position to remove
            
        Returns:
            True if position was in zone and block existed
        """
        if not self.contains(pos):
            return False
        if pos in self.blocks:
            del self.blocks[pos]
            return True
        return False
    
    def get_world_bounds(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Get world coordinate bounds of this zone.
        
        Returns:
            ((min_x, min_z), (max_x, max_z)) in world coordinates
        """
        if not self.chunk_coords:
            return ((0, 0), (0, 0))
            
        min_cx = min(c[0] for c in self.chunk_coords)
        max_cx = max(c[0] for c in self.chunk_coords)
        min_cz = min(c[1] for c in self.chunk_coords)
        max_cz = max(c[1] for c in self.chunk_coords)
        
        return (
            (min_cx * CHUNK_SIZE, min_cz * CHUNK_SIZE),
            ((max_cx + 1) * CHUNK_SIZE, (max_cz + 1) * CHUNK_SIZE)
        )
        
    def to_dict(self) -> dict:
        """Serialize zone for persistence/network."""
        return {
            "owner_id": self.owner_id,
            "chunk_coords": self.chunk_coords,
            "allowed_editors": self.allowed_editors,
            "blocks": {f"{k[0]},{k[1]},{k[2]}": v for k, v in self.blocks.items()},
            "name": self.name
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> "ClaimedZone":
        """Deserialize zone from persistence/network."""
        # Parse block positions back from string keys
        blocks = {}
        for key, val in data.get("blocks", {}).items():
            parts = key.split(",")
            pos = (int(parts[0]), int(parts[1]), int(parts[2]))
            blocks[pos] = val
        
        # Handle chunk_coords (could be list of lists from JSON)
        chunk_coords = [tuple(c) for c in data.get("chunk_coords", [])]
            
        return cls(
            owner_id=data["owner_id"],
            chunk_coords=chunk_coords,
            allowed_editors=data.get("allowed_editors", []),
            blocks=blocks,
            name=data.get("name", "Build Zone")
        )
