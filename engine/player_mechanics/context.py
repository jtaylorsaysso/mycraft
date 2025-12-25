"""Player context object for mechanics."""

from dataclasses import dataclass, field
from typing import Set, List, Optional, TYPE_CHECKING
from panda3d.core import LVector3f

if TYPE_CHECKING:
    from engine.ecs.world import World
    from engine.components.core import Transform
    from engine.physics import KinematicState

@dataclass
class InputState:
    """Snapshot of input state for a frame."""
    mouse_delta: tuple[float, float] = (0.0, 0.0)
    keys_down: Set[str] = field(default_factory=set)
    
    def is_key_down(self, key: str) -> bool:
        return key.lower() in self.keys_down
    
    # Convenience properties
    @property
    def forward(self) -> bool:
        return self.is_key_down('w')
    
    @property
    def back(self) -> bool:
        return self.is_key_down('s')
    
    @property
    def left(self) -> bool:
        return self.is_key_down('a')
    
    @property
    def right(self) -> bool:
        return self.is_key_down('d')
    
    @property
    def jump(self) -> bool:
        return self.is_key_down('space')
    
    @property
    def crouch(self) -> bool:
        return self.is_key_down('shift')


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
    
    # Shared state between mechanics
    camera_mode: str = 'third_person'
    
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
