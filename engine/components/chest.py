"""
Chest component for storing loot container state.
"""
from dataclasses import dataclass, field
from typing import List, Tuple
from engine.ecs.component import Component, register_component


@register_component
@dataclass
class ChestComponent(Component):
    """Component for chest entities that contain loot.
    
    Attributes:
        position: World block coordinates (x, y, z) of the chest
        items: List of item IDs contained in the chest
        is_open: Whether the chest has been looted
        poi_type: Source POI type (e.g., "camp_enemy", "shrine_challenge")
    """
    position: Tuple[int, int, int] = (0, 0, 0)
    items: List[str] = field(default_factory=list)
    is_open: bool = False
    poi_type: str = ""
