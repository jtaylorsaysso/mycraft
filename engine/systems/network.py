"""
Networking systems: Automatic Component Sync.
"""
from engine.ecs.system import System
from engine.ecs.component import Component, get_component_class
from engine.components.core import Transform, Health
from engine.core.logger import get_logger
from typing import Dict, Any, List

logger = get_logger(__name__)

class SyncSystem(System):
    """
    Automatically syncs marked components over the network.
    Uses existing MyCraft client/server infrastructure but adapts it to ECS.
    """
    
    def __init__(self, world, event_bus):
        super().__init__(world, event_bus)
        self.is_server = False
        self.network_client = None
        self.network_server = None
        
        # Components to automatically sync
        self.sync_registry = {
            Transform,
            Health
        }

    def initialize(self):
        # We hook into the existing network events if available
        # This will be wired up by the main game loop
        pass

    def update(self, dt: float):
        if not self.is_server and not self.network_client:
            return
            
        # If server: broadcast updates for dirty components
        if self.is_server and self.network_server:
            pass # TODO: Implement server replication logic
            
        # If client: send local player components to server
        if not self.is_server and self.network_client:
            self._sync_client_to_server()

    def _sync_client_to_server(self):
        """Send local entity updates to server."""
        # For now, we assume the player entity is tagged "player"
        player_id = self.world._tags.get("player")
        if not player_id:
            return
            
        # Get components to sync
        # In a real impl, we'd check for changes (dirty flag)
        transform = self.world.get_component(player_id, Transform)
        if transform:
            # Send position update (using existing protocol or new one)
            # self.network_client.send_position(transform.position)
            pass

    def apply_remote_update(self, entity_id: str, component_name: str, data: Dict[str, Any]):
        """Apply an update received from the network."""
        comp_class = get_component_class(component_name)
        if not comp_class:
            return
            
        component = self.world.get_component(entity_id, comp_class)
        if not component:
            # Create if missing? Or ignore?
            return
            
        # Update fields
        for key, value in data.items():
            if hasattr(component, key):
                setattr(component, key, value)
