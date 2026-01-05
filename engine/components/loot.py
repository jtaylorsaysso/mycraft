"""
Loot and Pickup components.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from engine.ecs.component import Component, register_component

@register_component
@dataclass
class LootComponent(Component):
    """Refers to loot dropped on death."""
    color_name: Optional[str] = None  # Name of color to drop (e.g. "red")
    # Future: item_ids, drop_chances

@register_component
@dataclass
class PickupComponent(Component):
    """Entity can be picked up by walking over it."""
    pickup_radius: float = 1.0
    auto_pickup: bool = True
    # If it's a color swatch:
    color_name: Optional[str] = None
    # If it's an item:
    item_id: Optional[str] = None
    
@register_component
@dataclass
class InventoryComponent(Component):
    """Player inventory for items."""
    items: List[str] = field(default_factory=list)
