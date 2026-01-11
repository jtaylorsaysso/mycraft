"""Claim Stake item for expanding player build zones.

A consumable item that creates a new ClaimedZone when used.
"""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class ClaimStake:
    """Item component for claim stake.
    
    When used (right-click), creates a new ClaimedZone at the
    target location if valid (not overlapping existing claims).
    
    Attributes:
        radius: Size of the zone to create (default 8)
        consumed: Whether the stake has been used
    """
    radius: int = 8
    consumed: bool = False
    
    def use(self, owner_id: str, position: Tuple[int, int, int], claim_system) -> bool:
        """Attempt to use the stake to create a zone.
        
        Args:
            owner_id: Entity ID of the player using the stake
            position: World position to place the claim
            claim_system: The ClaimSystem instance
            
        Returns:
            True if zone was created, False if failed (overlap, etc.)
        """
        if self.consumed:
            return False
            
        result = claim_system.claim_zone(owner_id, position, self.radius)
        if result:
            self.consumed = True
            return True
        return False


# Item registry entry for claim stake
CLAIM_STAKE_ITEM = {
    "id": "claim_stake",
    "name": "Claim Stake",
    "description": "Place to claim a new build zone",
    "category": "tool",
    "stackable": False,
    "max_stack": 1,
    "icon": "claim_stake",
    "component": ClaimStake
}
