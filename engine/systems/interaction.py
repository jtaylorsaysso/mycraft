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

    def on_pickup(self, event: Any):
        entity_id = event.entity_id
        item_type = event.item_type
        
        inventory = self.world.get_component(entity_id, Inventory)
        if not inventory:
            return

        # Simple add logic: find first empty slot or stackable slot
        # In a real implementation this would check max_stack and item types
        added = False
        for i, slot in enumerate(inventory.slots):
            if slot is None:
                inventory.slots[i] = item_type
                added = True
                break
            elif slot == item_type:
                # TODO: Implement stacking logic
                pass
                
        if added:
            logger.info(f"Entity {entity_id} picked up {item_type}")
            # If item was a world entity, destroy it
            item_entity = getattr(event, 'item_entity_id', None)
            if item_entity:
                self.world.destroy_entity(item_entity)

    def on_drop(self, event: Any):
        entity_id = event.entity_id
        slot_index = event.slot_index
        
        inventory = self.world.get_component(entity_id, Inventory)
        if not inventory or slot_index >= len(inventory.slots):
            return
            
        item = inventory.slots[slot_index]
        if item:
            inventory.slots[slot_index] = None
            
            # Spawn item in world
            transform = self.world.get_component(entity_id, Transform)
            if transform:
                # TODO: Spawn item entity at position
                self.event_bus.publish("on_item_spawn", item_type=item, position=transform.position)


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
