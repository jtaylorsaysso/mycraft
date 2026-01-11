"""Block placement mechanic for in-game building.

Allows players to place and remove blocks within claimed zones
during normal gameplay (outside the editor).
"""

from typing import Optional, Tuple
from panda3d.core import LVector3f

from engine.player_mechanics.base import PlayerMechanic
from engine.player_mechanics.context import PlayerContext
from engine.components.claimed_zone import ClaimedZone
from engine.core.logger import get_logger

logger = get_logger(__name__)


class BlockPlacerMechanic(PlayerMechanic):
    """Handles runtime block placement within claimed zones.
    
    This mechanic:
    - Toggles build mode on 'b' key
    - Places blocks on left click (when in build mode)
    - Removes blocks on right click (when in build mode)
    - Only allows edits within ClaimedZone boundaries
    """
    
    priority = 50  # After core movement, before UI
    exclusive = False
    
    def __init__(self, base):
        self.base = base
        self.enabled = False  # Build mode toggle
        self.world = None
        self.terrain_system = None
        self.selected_block = "stone"
        self._toggle_cooldown = 0.0
        
    def setup(self, base):
        """Called by coordinator during initialize phase."""
        self.base = base
        
    def initialize(self, player_id: str, world):
        """Called when player entity is created."""
        self.world = world
        self.player_id = player_id
        # Try to get terrain system from game
        if hasattr(self.base, 'terrain_system'):
            self.terrain_system = self.base.terrain_system
        
        # Listen to build mode events from FSM
        if world and hasattr(world, 'event_bus'):
            world.event_bus.subscribe("build_mode_changed", self._on_build_mode_changed)
        
        logger.info("🔨 BlockPlacer mechanic initialized")
        
    def can_handle(self, ctx: PlayerContext) -> bool:
        """Only active when build mode is enabled."""
        return self.enabled
        
    def update(self, ctx: PlayerContext) -> None:
        """Process block placement/removal inputs."""
        if not self.world or not ctx.input:
            return
            
        # Handle toggle with cooldown
        if self._toggle_cooldown > 0:
            self._toggle_cooldown -= ctx.dt
            
        # Check for toggle key (handled externally via check_toggle)
        
        if not self.enabled:
            logger.debug("BlockPlacer not enabled - press B to enter build mode")
            return
            
        # Get player's claimed zone
        player_zone = self._get_player_zone()
        if not player_zone:
            logger.debug("No claimed zone found for player - cannot place blocks")
            return
        
        logger.debug(f"BlockPlacer active, zone found: {player_zone.name}")
            
        # Handle placement on left click
        if "attack" in ctx.input.actions or "mouse1" in ctx.input.keys_down:
            logger.debug("Left click detected - attempting block placement")
            self._try_place_block(ctx, player_zone)
            
        # Handle removal on right click  
        if "mouse3" in ctx.input.keys_down:
            logger.debug("Right click detected - attempting block removal")
            self._try_remove_block(ctx, player_zone)
            
    def check_toggle(self, key: str) -> bool:
        """Check if build mode should be toggled.
        
        Call this from the game's input handling.
        Returns True if toggle happened.
        """
        if key == "b" and self._toggle_cooldown <= 0:
            self.enabled = not self.enabled
            self._toggle_cooldown = 0.3  # Debounce
            mode = "ON" if self.enabled else "OFF"
            logger.info(f"🔨 Build mode: {mode}")
            # Publish event for UI feedback
            if self.world and hasattr(self.world, 'event_bus'):
                self.world.event_bus.publish("build_mode_changed", enabled=self.enabled)
            return True
        return False
    
    def _on_build_mode_changed(self, enabled: bool):
        """Handle build mode state change from FSM.
        
        Args:
            enabled: True if entering build mode, False if exiting
        """
        self.enabled = enabled
        mode = "ON" if enabled else "OFF"
        logger.info(f"🔨 Build mode: {mode}")
        
    def try_place_stake(self, position: Tuple[int, int, int]) -> bool:
        """Try to place a claim stake at position.
        
        Args:
            position: World position for new zone center
            
        Returns:
            True if zone was created
        """
        if not self.world:
            return False
            
        # Get claim system from game
        claim_system = None
        if hasattr(self.world, 'base') and hasattr(self.world.base, 'claim_system'):
            claim_system = self.world.base.claim_system
            
        if not claim_system:
            logger.warning("Cannot place stake: ClaimSystem not found")
            return False
            
        # Try to create zone
        result = claim_system.claim_zone(self.player_id, position, radius=8)
        if result:
            logger.info(f"✅ Placed claim stake at {position}")
            if hasattr(self.world, 'event_bus'):
                self.world.event_bus.publish("claim_stake_placed", position=position)
            return True
        else:
            logger.warning(f"❌ Cannot place stake at {position} - overlaps existing zone")
            return False
        
    def set_block_type(self, block_type: str):
        """Set the block type to place."""
        self.selected_block = block_type
        
    def _get_player_zone(self) -> Optional[ClaimedZone]:
        """Get the ClaimedZone belonging to the current player."""
        if not self.world:
            return None
            
        # Search for zones owned by this player
        for entity_id in self.world.get_entities_with(ClaimedZone):
            zone = self.world.get_component(entity_id, ClaimedZone)
            if zone and zone.owner_id == self.player_id:
                return zone
        return None
        
    def _raycast_block_position(self, ctx: PlayerContext) -> Optional[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]:
        """Raycast to find block position under cursor.
        
        Returns:
            Tuple of (hit_pos, adjacent_pos) or None if no hit
        """
        if not self.terrain_system:
            return None
            
        # Get camera for raycast origin
        cam_pos = self.base.camera.getPos(self.base.render)
        cam_fwd = self.base.render.getRelativeVector(
            self.base.camera, 
            LVector3f(0, 1, 0)  # Forward in camera space
        )
        
        # Simple raycast (up to 10 blocks)
        for dist in range(1, 11):
            check_pos = cam_pos + cam_fwd * dist
            grid_pos = (
                round(check_pos.x),
                round(check_pos.y),
                round(check_pos.z)
            )
            
            # Check if solid block at this position
            if self._is_solid_at(grid_pos):
                # Return hit and adjacent (for placement)
                prev_pos = cam_pos + cam_fwd * (dist - 1)
                adj_pos = (
                    round(prev_pos.x),
                    round(prev_pos.y),
                    round(prev_pos.z)
                )
                return (grid_pos, adj_pos)
                
        return None
        
    def _is_solid_at(self, pos: Tuple[int, int, int]) -> bool:
        """Check if there's a solid block at position."""
        if not self.terrain_system:
            return False
        # Use terrain system's voxel lookup
        return self.terrain_system.get_block_at(pos[0], pos[1], pos[2]) is not None
        
    def _try_place_block(self, ctx: PlayerContext, zone: ClaimedZone):
        """Attempt to place a block."""
        ray_result = self._raycast_block_position(ctx)
        if not ray_result:
            return
            
        _, adj_pos = ray_result
        
        # Check if placement position is in zone
        if not zone.contains(adj_pos):
            logger.debug(f"Cannot place: outside zone bounds")
            return
            
        # Check permission (owner or editor)
        if not zone.can_edit(self.player_id):
            logger.debug(f"Cannot place: no permission")
            return
            
        # Place block in zone data
        if zone.add_block(adj_pos, self.selected_block):
            # Update world voxel grid
            if self.terrain_system:
                self.terrain_system.set_block_at(
                    adj_pos[0], adj_pos[1], adj_pos[2],
                    self.selected_block
                )
            logger.debug(f"Placed {self.selected_block} at {adj_pos}")
            
    def _try_remove_block(self, ctx: PlayerContext, zone: ClaimedZone):
        """Attempt to remove a block."""
        ray_result = self._raycast_block_position(ctx)
        if not ray_result:
            return
            
        hit_pos, _ = ray_result
        
        # Check if removal position is in zone
        if not zone.contains(hit_pos):
            logger.debug(f"Cannot remove: outside zone bounds")
            return
        
        # Check permission (owner or editor)
        if not zone.can_edit(self.player_id):
            logger.debug(f"Cannot remove: no permission")
            return
            
        # Remove from zone data
        if zone.remove_block(hit_pos):
            # Update world voxel grid
            if self.terrain_system:
                self.terrain_system.set_block_at(
                    hit_pos[0], hit_pos[1], hit_pos[2],
                    None  # Air
                )
            logger.debug(f"Removed block at {hit_pos}")
