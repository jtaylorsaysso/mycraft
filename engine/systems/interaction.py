from engine.ecs.system import System
from engine.components.core import Inventory, Transform
from engine.components.gameplay import Trigger
from engine.core.logger import get_logger
from typing import Any

logger = get_logger(__name__)

class InventorySystem(System):
    """
    Manages inventory interactions.
    Handles item pickup, dropping, and usage events.
    """
    
    def initialize(self):
        self.event_bus.subscribe("on_item_pickup", self.on_pickup)
        self.event_bus.subscribe("on_item_drop", self.on_drop)
        self.event_bus.subscribe("request_drop_item", self.on_request_drop)

    def on_request_drop(self, event: Any):
        """Handle request to drop selected item."""
        entity_id = event.entity_id
        inventory = self.world.get_component(entity_id, Inventory)
        if not inventory:
            return
            
        slot_index = inventory.selected_slot
        if 0 <= slot_index < len(inventory.slots):
            slot = inventory.slots[slot_index]
            if slot:
                item_type, count = slot
                # Drop entire stack
                inventory.slots[slot_index] = None
                
                # Spawn item in world
                transform = self.world.get_component(entity_id, Transform)
                if transform:
                    self.event_bus.publish("on_item_spawn", item_type=item_type, count=count, position=transform.position)


    def on_pickup(self, event: Any):
        entity_id = event.entity_id
        item_type = event.item_type
        count = getattr(event, 'count', 1)  # Default to 1 if not specified
        
        inventory = self.world.get_component(entity_id, Inventory)
        if not inventory:
            return

        # Try to stack with existing items first
        remaining = count
        for i, slot in enumerate(inventory.slots):
            if slot is not None:
                slot_item, slot_count = slot
                if slot_item == item_type and slot_count < inventory.max_stack:
                    # Can stack here
                    space_available = inventory.max_stack - slot_count
                    to_add = min(remaining, space_available)
                    inventory.slots[i] = (slot_item, slot_count + to_add)
                    remaining -= to_add
                    
                    if remaining == 0:
                        break
        
        # If we still have items remaining, find empty slots
        if remaining > 0:
            for i, slot in enumerate(inventory.slots):
                if slot is None:
                    to_add = min(remaining, inventory.max_stack)
                    inventory.slots[i] = (item_type, to_add)
                    remaining -= to_add
                    
                    if remaining == 0:
                        break
        
        # Log result
        picked_up = count - remaining
        if picked_up > 0:
            logger.info(f"Entity {entity_id} picked up {picked_up}x {item_type}")
            # If item was a world entity, destroy it
            item_entity = getattr(event, 'item_entity_id', None)
            if item_entity:
                self.world.destroy_entity(item_entity)
        
        if remaining > 0:
            logger.warning(f"Entity {entity_id} inventory full, {remaining}x {item_type} not picked up")

    def on_drop(self, event: Any):
        entity_id = event.entity_id
        slot_index = event.slot_index
        count = getattr(event, 'count', None)  # None means drop entire stack
        
        inventory = self.world.get_component(entity_id, Inventory)
        if not inventory or slot_index >= len(inventory.slots):
            return
            
        slot = inventory.slots[slot_index]
        if slot:
            item_type, slot_count = slot
            
            # Determine how many to drop
            drop_count = count if count is not None else slot_count
            drop_count = min(drop_count, slot_count)  # Can't drop more than we have
            
            # Update or clear slot
            if drop_count >= slot_count:
                inventory.slots[slot_index] = None
            else:
                inventory.slots[slot_index] = (item_type, slot_count - drop_count)
            
            # Spawn item in world
            transform = self.world.get_component(entity_id, Transform)
            if transform:
                self.event_bus.publish("on_item_spawn", item_type=item_type, count=drop_count, position=transform.position)


class TriggerSystem(System):
    """
    Detects entity overlap with Trigger zones.
    Fires on_enter and on_exit events.
    """
    
    def update(self, dt: float):
        trigger_entities = self.world.get_entities_with(Trigger, Transform)
        moving_entities = self.world.get_entities_with(Transform) # Check all moving things
        
        for tid in trigger_entities:
            trigger = self.world.get_component(tid, Trigger)
            t_transform = self.world.get_component(tid, Transform)
            
            # Simple AABB check
            # In real implementation, use physics engine collision events instead of separate check
            # But for simplicity in this engine, we do a quick bounds check here
            
            t_pos = t_transform.position
            # Effective bounds in world space
            min_bound = t_pos + trigger.bounds_min
            max_bound = t_pos + trigger.bounds_max
            
            for eid in moving_entities:
                if eid == tid: continue # Don't trigger self
                
                e_transform = self.world.get_component(eid, Transform)
                e_pos = e_transform.position
                
                # Check point vs AABB
                is_inside = (
                    min_bound.x <= e_pos.x <= max_bound.x and
                    min_bound.y <= e_pos.y <= max_bound.y and
                    min_bound.z <= e_pos.z <= max_bound.z
                )
                
                # Logic to detect state change (enter vs exit) would require storing previous state
                # For this MVP, we just fire 'on_zone_stay' or assume per-frame checks are okay
                if is_inside:
                    self.event_bus.publish("on_zone_enter", zone_id=tid, entity_id=eid)
                    if trigger.one_shot and not trigger.triggered:
                        trigger.triggered = True
                        # Potentially disable trigger
