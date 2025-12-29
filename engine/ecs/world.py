"""
World class managing entities and systems.
"""
from typing import Dict, List, Type, TypeVar, Optional, Set, Any
import uuid
from engine.ecs.component import Component
from engine.ecs.system import System
from engine.ecs.events import EventBus
from engine.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=Component)

class World:
    """
    The main container for the ECS.
    Manages entities, components, strings systems together.
    """
    def __init__(self):
        self.event_bus = EventBus()
        self._systems: List[System] = []
        self._pending_systems: List[System] = []  # Systems waiting for dependencies
        
        # Entity ID -> {ComponentType -> ComponentInstance}
        self._entities: Dict[str, Dict[Type[Component], Component]] = {}
        
        # ComponentType -> Set[EntityID] (for fast querying)
        self._component_index: Dict[Type[Component], Set[str]] = {}
        
        # Tag -> EntityID (for unique named entities like 'player')
        self._tags: Dict[str, str] = {}

    def create_entity(self, tag: Optional[str] = None) -> str:
        """Create a new empty entity and return its ID."""
        entity_id = str(uuid.uuid4())
        self._entities[entity_id] = {}
        
        if tag:
            self._tags[tag] = entity_id
            # Check if any pending systems are now satisfied
            self._check_pending_systems()
            
        return entity_id

    def get_entity_by_tag(self, tag: str) -> Optional[str]:
        """Get entity ID by tag name."""
        return self._tags.get(tag)

    def register_tag(self, entity_id: str, tag: str):
        """Register a tag for an existing entity.
        
        This is useful for delaying tag assignment until after components 
        are initialized, ensuring systems don't wake up too early.
        """
        if entity_id not in self._entities:
            raise KeyError(f"Entity {entity_id} does not exist")
            
        self._tags[tag] = entity_id
        # Check if any pending systems are now satisfied
        self._check_pending_systems()

    def destroy_entity(self, entity_id: str):
        """Remove an entity and all its components."""
        if entity_id not in self._entities:
            return
            
        # Clean up indices
        for component_type in self._entities[entity_id]:
            if component_type in self._component_index:
                self._component_index[component_type].discard(entity_id)
                
        # Remove from tags if present
        tags_to_remove = [k for k, v in self._tags.items() if v == entity_id]
        for t in tags_to_remove:
            del self._tags[t]
            
        del self._entities[entity_id]

    def add_component(self, entity_id: str, component: Component):
        """Add a component to an entity."""
        if entity_id not in self._entities:
            raise KeyError(f"Entity {entity_id} does not exist")
            
        component_type = type(component)
        self._entities[entity_id][component_type] = component
        
        if component_type not in self._component_index:
            self._component_index[component_type] = set()
        self._component_index[component_type].add(entity_id)

    def remove_component(self, entity_id: str, component_type: Type[T]):
        """Remove a component from an entity."""
        if entity_id in self._entities and component_type in self._entities[entity_id]:
            del self._entities[entity_id][component_type]
            if component_type in self._component_index:
                self._component_index[component_type].discard(entity_id)

    def get_component(self, entity_id: str, component_type: Type[T]) -> Optional[T]:
        """Get a specific component for an entity."""
        if entity_id not in self._entities:
            return None
        return self._entities[entity_id].get(component_type)

    def has_component(self, entity_id: str, component_type: Type[Component]) -> bool:
        """Check if entity has a component."""
        return entity_id in self._entities and component_type in self._entities[entity_id]

    def get_entities_with(self, *component_types: Type[Component]) -> Set[str]:
        """Get set of entity IDs that possess ALL specified component types."""
        if not component_types:
            return set(self._entities.keys())
            
        result = None
        for ct in component_types:
            entities = self._component_index.get(ct, set())
            if result is None:
                result = entities.copy()
            else:
                result &= entities
                
        return result or set()

    def get_components(self, entity_id: str) -> Dict[Type[Component], Component]:
        """Get all components for an entity."""
        return self._entities.get(entity_id, {})

    def add_system(self, system: System):
        """Add a logic system to the world."""
        self._systems.append(system)
        system.initialize()
        logger.info(f"Initialized ECS System: {system.__class__.__name__}")
        
        # Check if system has dependencies
        dependencies = system.get_dependencies()
        if dependencies:
            # System has dependencies - check if satisfied
            if self._dependencies_satisfied(system):
                system.on_ready()
                logger.info(f"System ready immediately: {system.__class__.__name__}")
            else:
                # Add to pending list
                self._pending_systems.append(system)
                logger.info(f"System pending dependencies {dependencies}: {system.__class__.__name__}")
        else:
            # No dependencies - ready immediately
            system.on_ready()
            logger.info(f"System ready (no dependencies): {system.__class__.__name__}")
    
    def get_system_by_type(self, system_name: str) -> Optional[System]:
        """Get a system by its class name.
        
        Args:
            system_name: Name of the system class (e.g., "TerrainSystem")
            
        Returns:
            System instance or None if not found
        """
        for system in self._systems:
            if system.__class__.__name__ == system_name:
                return system
        return None

    def update(self, dt: float):
        """Update all systems."""
        # Check pending systems periodically (in case dependencies appear)
        self._check_pending_systems()
        
        # Update only ready systems
        for system in self._systems:
            if system.enabled and system.ready:
                system.update(dt)
    
    def _dependencies_satisfied(self, system: System) -> bool:
        """Check if all dependencies for a system are satisfied.
        
        Args:
            system: System to check dependencies for
            
        Returns:
            True if all required entity tags exist
        """
        dependencies = system.get_dependencies()
        for tag in dependencies:
            if tag not in self._tags:
                return False
        return True
    
    def _check_pending_systems(self):
        """Check if any pending systems have their dependencies satisfied."""
        for system in list(self._pending_systems):
            if self._dependencies_satisfied(system):
                system.on_ready()
                self._pending_systems.remove(system)
                logger.info(f"System ready: {system.__class__.__name__}")
