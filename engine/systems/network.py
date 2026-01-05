"""
Networking systems: Automatic Component Sync.
"""
from engine.ecs.system import System
from engine.ecs.component import Component, get_component_class
from engine.components.core import Transform, Health
from engine.components.avatar_colors import AvatarColors
from engine.core.logger import get_logger
from typing import Dict, Any, List
import json

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
            Health,
            AvatarColors
        }
        
        # Track dirty components (changed since last sync)
        self.dirty_entities: set = set()
        
        # Sync rate limiting
        self.sync_interval = 0.05  # Sync every 50ms (20Hz)
        self.time_since_sync = 0.0

    def initialize(self):
        # Subscribe to component change events if available
        # For now, we'll sync all entities periodically
        pass

    def mark_dirty(self, entity_id: str):
        """Mark an entity as having changed components."""
        self.dirty_entities.add(entity_id)

    def update(self, dt: float):
        if not self.is_server and not self.network_client:
            return
        
        self.time_since_sync += dt
        
        # Rate limit syncing
        if self.time_since_sync < self.sync_interval:
            return
        
        self.time_since_sync = 0.0
            
        # If server: broadcast updates for all entities with synced components
        if self.is_server and self.network_server:
            self._sync_server_to_clients()
            
        # If client: send local player components to server
        if not self.is_server and self.network_client:
            self._sync_client_to_server()

    def _sync_server_to_clients(self):
        """Broadcast entity component updates to all clients."""
        # Collect all entities with syncable components
        updates = []
        
        for entity_id in self.world._entities:
            entity_data = {
                "entity_id": entity_id,
                "components": {}
            }
            
            has_synced_components = False
            
            for comp_class in self.sync_registry:
                component = self.world.get_component(entity_id, comp_class)
                if component:
                    has_synced_components = True
                    # Serialize component data
                    entity_data["components"][comp_class.__name__] = self._serialize_component(component)
            
            if has_synced_components:
                updates.append(entity_data)
        
        if updates:
            # Send via existing server infrastructure
            message = json.dumps({
                "type": "component_sync",
                "entities": updates
            }) + "\n"
            
            # Broadcast to all clients
            # Note: This requires the server to expose a broadcast method
            # For now, we'll assume it's available via the network_server
            if hasattr(self.network_server, 'broadcast_to_all'):
                import asyncio
                asyncio.create_task(self.network_server.broadcast_to_all(message))
        
        # Clear dirty flags after sync
        self.dirty_entities.clear()

    def _serialize_component(self, component: Component) -> Dict[str, Any]:
        """Convert a component to a JSON-serializable dict."""
        data = {}
        
        # Handle Transform specially (LVector3f needs conversion)
        if isinstance(component, Transform):
            pos = component.position
            data = {
                "position": [pos.x, pos.y, pos.z] if pos else [0, 0, 0]
            }
        # Handle Health
        elif isinstance(component, Health):
            data = {
                "current": component.current,
                "max_hp": component.max_hp
            }
        else:
            # Generic serialization for other components
            for attr in dir(component):
                if not attr.startswith('_') and not callable(getattr(component, attr)):
                    value = getattr(component, attr)
                    # Only serialize basic types
                    if isinstance(value, (int, float, str, bool, list, dict)):
                        data[attr] = value
        
        return data

    def _sync_client_to_server(self):
        """Send local entity updates to server."""
        # For now, we assume the player entity is tagged "player"
        player_id = self.world._tags.get("player")
        if not player_id:
            return
            
        # Get components to sync
        transform = self.world.get_component(player_id, Transform)
        if transform:
            # Send position update (using existing protocol)
            # The existing client already sends position updates
            # This is redundant with the existing system, so we skip it
            pass
            
        colors = self.world.get_component(player_id, AvatarColors)
        if colors:
             # Send color updates?
             # Usually client authority for customization, or server?
             # For now, assume client is authority on their own colors (e.g. customization UI)
             # But actually, finding loot happens on server.
             # So Server -> Client sync is the main one.
             pass

    def apply_remote_update(self, entity_id: str, component_name: str, data: Dict[str, Any]):
        """Apply an update received from the network."""
        comp_class = get_component_class(component_name)
        if not comp_class:
            logger.warning(f"Unknown component class: {component_name}")
            return
            
        component = self.world.get_component(entity_id, comp_class)
        if not component:
            # Create component if missing
            component = comp_class()
            self.world.add_component(entity_id, component)
            
        # Update fields based on component type
        if isinstance(component, Transform):
            from panda3d.core import LVector3f
            if "position" in data:
                pos = data["position"]
                component.position = LVector3f(pos[0], pos[1], pos[2])
        elif isinstance(component, Health):
            if "current" in data:
                component.current = data["current"]
            if "max_hp" in data:
                component.max_hp = data["max_hp"]
        elif isinstance(component, AvatarColors):
             if "body_color" in data:
                 component.body_color = tuple(data["body_color"])
             if "bone_colors" in data:
                 # JSON keys are always strings, which fits bone names
                 # Values might come in as lists, need tuples for Panda3D friendliness sometimes?
                 # Panda3D accepts lists for color usually.
                 component.bone_colors = data["bone_colors"]
             if "unlocked_colors" in data:
                 component.unlocked_colors = data["unlocked_colors"]
             if "temporary_color" in data:
                 component.temporary_color = tuple(data["temporary_color"]) if data["temporary_color"] else None
        else:
            # Generic update for other components
            for key, value in data.items():
                if hasattr(component, key):
                    setattr(component, key, value)
