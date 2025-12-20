"""
Logic systems: Pathfinding, Timer.
"""
from typing import List
from engine.ecs.system import System
from engine.ecs.events import Event
from engine.components.core import Transform
from engine.components.gameplay import Pathfinder, Timer
from ursina import Vec3
import math

class PathfindingSystem(System):
    """
    Simple A* pathfinding on voxel grid.
    For this MVP, we implement a direct line-of-sight moveto as a placeholder
    until we expose the voxel world grid to this layer.
    """
    
    def update(self, dt: float):
        entities = self.world.get_entities_with(Pathfinder, Transform)
        for entity_id in entities:
            pathfinder = self.world.get_component(entity_id, Pathfinder)
            transform = self.world.get_component(entity_id, Transform)
            
            target_pos = pathfinder.target_position
            
            # If following an entity, update target position
            if pathfinder.target_entity:
                target_transform = self.world.get_component(pathfinder.target_entity, Transform)
                if target_transform:
                    target_pos = target_transform.position
            
            if not target_pos:
                continue
                
            # Move towards target
            direction = target_pos - transform.position
            dist = direction.length()
            
            if dist <= pathfinder.arrival_distance:
                # Arrived
                continue
                
            # Normalize and move
            if dist > 0:
                direction = direction.normalized()
                
            # Update position
            # Note: real implementation would check physics/collision
            move_amount = direction * pathfinder.speed * dt
            transform.position += move_amount
            
            # Look at target
            # transform.look_at(target_pos) # Requires ursina entity logic which we don't have here yet

class TimerSystem(System):
    """
    Updates Timer components and fires events on completion.
    """
    
    def update(self, dt: float):
        entities = self.world.get_entities_with(Timer)
        for entity_id in entities:
            timer = self.world.get_component(entity_id, Timer)
            
            if not timer.active:
                continue
                
            timer.elapsed += dt
            
            if timer.elapsed >= timer.duration:
                # Fire event
                self.event_bus.publish(
                    timer.on_complete_event, 
                    entity_id=entity_id,
                    timer_component=timer
                )
                
                if timer.loop:
                    timer.elapsed = 0
                else:
                    timer.active = False
