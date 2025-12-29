"""
Block definition API.
"""
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class Block:
    """
    Defines a voxel block type.
    """
    id: str
    texture_tile: Tuple[int, int]
    color: str = "#FFFFFF"
    solid: bool = True
    transparent: bool = False
    breakable: bool = True
    hardness: float = 1.0
    drop: Optional[str] = None
