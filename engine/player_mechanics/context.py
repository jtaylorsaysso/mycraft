"""Player context object for mechanics."""

from dataclasses import dataclass, field
from typing import Set, List, Optional, TYPE_CHECKING
from panda3d.core import LVector3f
from engine.input.keybindings import InputAction

if TYPE_CHECKING:
    from engine.ecs.world import World
    from engine.components.core import Transform
    from engine.physics import KinematicState

@dataclass
class InputState:
    """Snapshot of input state for a frame."""
    mouse_delta: tuple[float, float] = (0.0, 0.0)
    scroll_delta: float = 0.0
    keys_down: Set[str] = field(default_factory=set)
    actions: Set[InputAction] = field(default_factory=set)
    
    def is_key_down(self, key: str) -> bool:
        return key.lower() in self.keys_down
    
    def is_action_active(self, action: InputAction) -> bool:
        return action in self.actions
    
    # Convenience properties
    @property
    def forward(self) -> bool:
        return self.is_action_active(InputAction.MOVE_FORWARD)
    
    @property
    def back(self) -> bool:
        return self.is_action_active(InputAction.MOVE_BACK)
    
    @property
    def left(self) -> bool:
        return self.is_action_active(InputAction.MOVE_LEFT)
    
    @property
    def right(self) -> bool:
        return self.is_action_active(InputAction.MOVE_RIGHT)
    
    @property
    def jump(self) -> bool:
        return self.is_action_active(InputAction.JUMP)
    
    @property
    def crouch(self) -> bool:
        # Context sensitive: Slide or Crouch
        return (self.is_action_active(InputAction.SLIDE) or 
                self.is_action_active(InputAction.DODGE))


@dataclass
class PlayerContext:
    """Context object passed to all mechanics."""
    
    # Core references
    world: 'World'
    player_id: str
    transform: 'Transform'
    state: 'KinematicState'
    dt: float
    
    # Input state (populated by InputMechanic)
    input: InputState = field(default_factory=InputState)
    
    # Cached system references (populated by coordinator)
    terrain_system: Optional[object] = None
    water_system: Optional[object] = None
    
    # Transition requests
    _mechanic_requests: List[str] = field(default_factory=list)
    
    # Helpers
    def request_mechanic(self, name: str) -> None:
        """Request a specific mechanic for next frame."""
        self._mechanic_requests.append(name)
    
    def is_mechanic_requested(self, name: str) -> bool:
        """Check if mechanic was requested."""
        return name in self._mechanic_requests
    
    def clear_requests(self) -> None:
        """Clear mechanic requests (called by coordinator)."""
        self._mechanic_requests.clear()
    
    def update_refs(self, transform: 'Transform', state: 'KinematicState', dt: float) -> None:
        """Update core references in-place without reallocating.
        
        Args:
            transform: Updated Transform component
            state: Updated KinematicState component
            dt: Delta time for this frame
        """
        self.transform = transform
        self.state = state
        self.dt = dt
