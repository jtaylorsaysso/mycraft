"""Water physics system for buoyancy and swimming."""

from engine.ecs.system import System
from engine.components.core import Transform
from panda3d.core import LVector3f
from typing import Optional


from engine.physics.kinematic import KinematicState
from engine.physics.constants import WATER_DRAG, WATER_MULTIPLIER


class WaterPhysicsSystem(System):
    """Handles buoyancy, swimming, and underwater physics."""
    
    # Physics constants (imported from engine.physics.constants where applicable)
    BUOYANCY_FORCE = 15.0        # Upward force in water
    # SWIM_UP/DOWN forces could also be moved to constants if they are universal
    SWIM_UP_FORCE = 8.0          
    SWIM_DOWN_FORCE = 6.0        
    
    def __init__(self, world, event_bus):
        super().__init__(world, event_bus)
        self.water_blocks = {}  # (x, y, z) -> water_level mapping
        
    def register_water_block(self, x: int, y: int, z: int, level: int = 8):
        """Register a water block in the world.
        
        Args:
            x, y, z: Block position
            level: Water level (1-8, where 8 is full)
        """
        self.water_blocks[(x, y, z)] = level
    
    def unregister_water_block(self, x: int, y: int, z: int):
        """Remove a water block from tracking."""
        self.water_blocks.pop((x, y, z), None)
    
    def is_position_in_water(self, pos: LVector3f) -> bool:
        """Check if a position is inside a water block."""
        block_x = int(pos.x)
        block_y = int(pos.z)  # Note: Panda3D uses Z-up
        block_z = int(pos.y)
        
        return (block_x, block_y, block_z) in self.water_blocks
    
    def get_submersion_level(self, position: LVector3f, entity_height: float = 1.8) -> float:
        """Calculate how submerged an entity is.
        
        Args:
            position: Entity position (feet)
            entity_height: Height of entity
            
        Returns:
            Submersion level from 0.0 (not in water) to 1.0 (fully submerged)
        """
        feet_in_water = self.is_position_in_water(position)
        head_pos = LVector3f(position.x, position.y, position.z + entity_height)
        head_in_water = self.is_position_in_water(head_pos)
        
        if head_in_water:
            return 1.0  # Fully submerged
        elif feet_in_water:
            # Partial submersion (simplified - could be more accurate)
            return 0.5
        return 0.0
    
    def update(self, dt: float):
        """Apply water physics to entities."""
        # Get all entities with Transform
        entities = self.world.get_entities_with(Transform)
        
        for entity_id in entities:
            transform = self.world.get_component(entity_id, Transform)
            if not transform:
                continue
            
            # Check submersion
            submersion = self.get_submersion_level(transform.position)
            
            if submersion > 0:
                self.apply_water_physics(entity_id, transform, submersion, dt)
    
    def apply_water_physics(self, entity_id: str, transform: Transform, submersion: float, dt: float):
        """Apply buoyancy and resistance to an entity in water.
        
        Args:
            entity_id: Entity ID
            transform: Entity transform component
            submersion: Submersion level (0-1)
            dt: Delta time
        """
        # Try to get velocity from entity
        state = self.world.get_component(entity_id, KinematicState)
        if not state:
            # If no physics state, we fall back to position manipulation or skip
            # For this engine, we prefer entities have KinematicState for physics
            return
            
        # Simple buoyancy: affect vertical velocity
        # We use a simple force-like application: velocity_y += force * dt
        state.velocity_y += self.BUOYANCY_FORCE * submersion * dt
        
        # Apply water drag (imported from constants)
        # This affects horizontal and vertical velocity
        drag_factor = max(0.0, 1.0 - WATER_DRAG * dt)
        state.velocity_x *= drag_factor
        state.velocity_z *= drag_factor
        state.velocity_y *= drag_factor  # Vertical drag too
        
        # TODO: Apply water resistance to horizontal velocity
        # TODO: Hook into input system for swim controls
        
        # Emit event for other systems to react
        self.event_bus.emit("entity_in_water", {
            "entity_id": entity_id,
            "submersion": submersion
        })
