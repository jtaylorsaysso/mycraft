"""Base class for player mechanics using composition pattern."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from engine.player_mechanics.context import PlayerContext

class PlayerMechanic(ABC):
    """Base class for player movement/control mechanics.
    
    Mechanics are composable behaviors that handle specific aspects
    of player control (input, movement, camera, etc).
    
    Mechanics run in priority order and can be exclusive.
    """
    
    # Priority for execution order (higher runs first)
    priority: int = 50
    
    # If True, stops processing remaining mechanics this frame
    exclusive: bool = False
    
    def can_handle(self, ctx: 'PlayerContext') -> bool:
        """Return True if this mechanic should run this frame.
        
        Args:
            ctx: Player context with state and input
            
        Returns:
            True if this mechanic's update() should be called
        """
        return True
    
    @abstractmethod
    def update(self, ctx: 'PlayerContext') -> None:
        """Update player based on this mechanic.
        
        Args:
            ctx: Player context - modify state/transform as needed
        """
        pass
        
    def initialize(self, player_id: int, world: Any) -> None:
        """Called when system is ready.
        
        Args:
            player_id: The player entity ID
            world: The game world
        """
        self._player_id = player_id
        self.world = world
    
    def cleanup(self) -> None:
        """Called when mechanic is removed."""
        pass
