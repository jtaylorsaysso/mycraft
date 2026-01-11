"""Claim System - manages player build zones.

This ECS system handles:
- Zone visualization (boundary rendering)
- Zone claiming via items/interactions
- Chunk-based claim registry for O(1) lookup
"""

from typing import Dict, List, Optional, Tuple
from panda3d.core import NodePath, LineSegs, Vec4

from engine.ecs.system import System
from engine.components.claimed_zone import ClaimedZone, CHUNK_SIZE
from engine.components.core import Transform
from engine.core.logger import get_logger

logger = get_logger(__name__)


class ClaimSystem(System):
    """Manages player-claimed build zones.
    
    Features:
    - Chunk-aligned zones for efficient networking
    - O(1) ownership lookup via chunk registry
    - Renders wireframe boundaries at chunk edges
    """
    
    def __init__(self, world, event_bus, render_node: NodePath):
        """Initialize the claim system.
        
        Args:
            world: ECS world instance
            event_bus: Event bus for communication
            render_node: Panda3D node for rendering zone visuals
        """
        super().__init__(world, event_bus)
        self.render_node = render_node
        
        # Visual nodes for zone boundaries
        self._zone_visuals: Dict[str, NodePath] = {}
        
        # Chunk registry: (chunk_x, chunk_z) -> zone entity ID
        self._chunk_registry: Dict[Tuple[int, int], str] = {}
        
        # Subscribe to events
        if event_bus:
            event_bus.subscribe("claim_chunk_request", self._on_claim_chunk_request)
            
    def _on_claim_chunk_request(self, player_id: str, chunk_x: int, chunk_z: int):
        """Handle request to claim a chunk.
        
        Args:
            player_id: Entity ID of claiming player
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
        """
        return self.claim_chunk(player_id, chunk_x, chunk_z)
        
    def claim_chunk(self, player_id: str, chunk_x: int, chunk_z: int) -> Optional[str]:
        """Claim a single chunk for a player.
        
        If player already has a zone, adds chunk to existing zone.
        Otherwise creates a new zone entity.
        
        Args:
            player_id: Entity ID of claiming player
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            
        Returns:
            Entity ID of zone, or None if chunk already claimed
        """
        chunk_key = (chunk_x, chunk_z)
        
        # Check if chunk is already claimed
        if chunk_key in self._chunk_registry:
            logger.warning(f"Cannot claim: chunk {chunk_key} already owned")
            return None
            
        # Check if player already has a zone
        existing_zone_entity = None
        existing_zone = None
        for entity_id in self.world.get_entities_with(ClaimedZone):
            zone = self.world.get_component(entity_id, ClaimedZone)
            if zone and zone.owner_id == player_id:
                existing_zone_entity = entity_id
                existing_zone = zone
                break
                
        if existing_zone:
            # Add chunk to existing zone
            existing_zone.chunk_coords.append(chunk_key)
            self._chunk_registry[chunk_key] = existing_zone_entity
            
            # Update visual
            self._remove_zone_visual(existing_zone_entity)
            self._create_zone_visual(existing_zone_entity, existing_zone)
            
            logger.info(f"✅ Added chunk {chunk_key} to existing zone")
            return existing_zone_entity
        else:
            # Create new zone entity
            zone_entity = self.world.create_entity()
            zone = ClaimedZone(
                owner_id=player_id,
                chunk_coords=[chunk_key],
                name=f"Zone_{zone_entity[:8]}"
            )
            self.world.add_component(zone_entity, zone)
            self._chunk_registry[chunk_key] = zone_entity
            
            # Create visual boundary
            self._create_zone_visual(zone_entity, zone)
            
            logger.info(f"✅ Created new zone for {player_id} at chunk {chunk_key}")
            return zone_entity
    
    def claim_zone_at_position(self, player_id: str, world_pos: Tuple[float, float, float]) -> Optional[str]:
        """Claim the chunk containing a world position.
        
        Convenience method for claiming chunk at player's location.
        
        Args:
            player_id: Entity ID of claiming player
            world_pos: World coordinates (x, y, z)
            
        Returns:
            Entity ID of zone, or None if failed
        """
        chunk_x = int(world_pos[0]) // CHUNK_SIZE
        chunk_z = int(world_pos[2]) // CHUNK_SIZE  # Z is horizontal
        return self.claim_chunk(player_id, chunk_x, chunk_z)
    
    # Legacy method for backward compatibility with spawn_player
    def claim_zone(self, player_id: str, center: Tuple[int, int, int], radius: int = 8) -> Optional[str]:
        """Legacy method - claims chunk at center position.
        
        Kept for backward compatibility with game.py spawn_player.
        """
        return self.claim_zone_at_position(player_id, center)
        
    def is_chunk_claimed(self, chunk_x: int, chunk_z: int) -> bool:
        """Check if a chunk is claimed."""
        return (chunk_x, chunk_z) in self._chunk_registry
        
    def get_chunk_owner(self, chunk_x: int, chunk_z: int) -> Optional[str]:
        """Get the zone entity that owns a chunk."""
        return self._chunk_registry.get((chunk_x, chunk_z))
        
    def get_zone_at_position(self, pos: Tuple[int, int, int]) -> Optional[ClaimedZone]:
        """Get the zone containing a world position."""
        chunk_x = pos[0] // CHUNK_SIZE
        chunk_z = pos[2] // CHUNK_SIZE
        
        zone_entity = self._chunk_registry.get((chunk_x, chunk_z))
        if zone_entity:
            return self.world.get_component(zone_entity, ClaimedZone)
        return None
        
    def _create_zone_visual(self, entity_id: str, zone: ClaimedZone):
        """Create wireframe boundary visual for a zone's chunks."""
        if not zone.chunk_coords:
            return
            
        lines = LineSegs(f"zone_boundary_{entity_id}")
        lines.setThickness(2.0)
        lines.setColor(Vec4(0.2, 0.8, 0.3, 0.8))  # Green tint
        
        # Draw boundary for each chunk
        for chunk_x, chunk_z in zone.chunk_coords:
            world_x = chunk_x * CHUNK_SIZE
            world_z = chunk_z * CHUNK_SIZE
            
            # Get ground level (approximate)
            ground_y = 0
            h = 32  # Height of boundary
            
            # Bottom square (at ground)
            lines.moveTo(world_x, world_z, ground_y)
            lines.drawTo(world_x + CHUNK_SIZE, world_z, ground_y)
            lines.drawTo(world_x + CHUNK_SIZE, world_z + CHUNK_SIZE, ground_y)
            lines.drawTo(world_x, world_z + CHUNK_SIZE, ground_y)
            lines.drawTo(world_x, world_z, ground_y)
            
            # Top square
            lines.moveTo(world_x, world_z, ground_y + h)
            lines.drawTo(world_x + CHUNK_SIZE, world_z, ground_y + h)
            lines.drawTo(world_x + CHUNK_SIZE, world_z + CHUNK_SIZE, ground_y + h)
            lines.drawTo(world_x, world_z + CHUNK_SIZE, ground_y + h)
            lines.drawTo(world_x, world_z, ground_y + h)
            
            # Vertical edges (corners only)
            for dx, dz in [(0, 0), (CHUNK_SIZE, 0), (CHUNK_SIZE, CHUNK_SIZE), (0, CHUNK_SIZE)]:
                lines.moveTo(world_x + dx, world_z + dz, ground_y)
                lines.drawTo(world_x + dx, world_z + dz, ground_y + h)
            
        geom = lines.create()
        visual = self.render_node.attachNewNode(geom)
        self._zone_visuals[entity_id] = visual
        
    def _remove_zone_visual(self, entity_id: str):
        """Remove visual for a zone."""
        if entity_id in self._zone_visuals:
            self._zone_visuals[entity_id].removeNode()
            del self._zone_visuals[entity_id]
            
    def update(self, dt: float):
        """Update claim system each frame."""
        # Could add visual effects, zone decay, etc.
        pass
        
    def get_zones_for_player(self, player_id: str) -> List[ClaimedZone]:
        """Get all zones owned by a player."""
        zones = []
        for entity_id in self.world.get_entities_with(ClaimedZone):
            zone = self.world.get_component(entity_id, ClaimedZone)
            if zone and zone.owner_id == player_id:
                zones.append(zone)
        return zones
        
    def cleanup(self):
        """Clean up all zone visuals."""
        for visual in self._zone_visuals.values():
            visual.removeNode()
        self._zone_visuals.clear()
        self._chunk_registry.clear()
