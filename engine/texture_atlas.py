"""Texture atlas system for efficient block rendering.

This module handles loading and UV coordinate calculation for the terrain.png
texture atlas (classic Minecraft 16x16 tile format).
"""

from typing import Optional
from ursina import Vec2, Texture, load_texture
from util.logger import get_logger


class TextureAtlas:
    """Manages texture atlas loading and UV coordinate mapping.
    
    The atlas is a 256x256 image containing a 16x16 grid of 16x16 pixel tiles.
    Tiles are indexed 0-255 in row-major order from top-left.
    """
    
    GRID_SIZE = 16  # 16x16 tiles
    TILE_SIZE = 1.0 / GRID_SIZE  # Normalized tile size (1/16)
    
    def __init__(self, image_path: str):
        """Initialize the texture atlas.
        
        Args:
            image_path: Path to the texture atlas image (e.g., "Spritesheets/terrain.png")
        """
        self.logger = get_logger("texture_atlas")
        self.image_path = image_path
        self._texture: Optional[Texture] = None
        
        # Try to load the texture
        try:
            self._texture = load_texture(image_path)
            self.logger.info(f"Loaded texture atlas from {image_path}")
        except Exception as e:
            self.logger.error(f"Failed to load texture atlas from {image_path}: {e}")
            self._texture = None
    
    def get_texture(self) -> Optional[Texture]:
        """Get the loaded texture object.
        
        Returns:
            Texture object if loaded successfully, None otherwise
        """
        return self._texture
    
    def is_loaded(self) -> bool:
        """Check if the texture atlas loaded successfully.
        
        Returns:
            True if texture is loaded and ready to use
        """
        return self._texture is not None
    
    def get_tile_uvs(self, tile_index: int) -> list[Vec2]:
        """Get UV coordinates for a tile as a quad (4 vertices).
        
        Args:
            tile_index: Tile index (0-255) in row-major order
            
        Returns:
            List of 4 Vec2 UV coordinates for quad vertices in order:
            [bottom-left, bottom-right, top-right, top-left]
            
        Raises:
            ValueError: If tile_index is out of range
        """
        if not (0 <= tile_index < 256):
            raise ValueError(f"Tile index {tile_index} out of range (0-255)")
        
        # Calculate row and column from tile index
        row = tile_index // self.GRID_SIZE
        col = tile_index % self.GRID_SIZE
        
        # Calculate normalized UV coordinates
        # Note: OpenGL uses bottom-left origin, so we need to flip Y
        u_min = col * self.TILE_SIZE
        u_max = (col + 1) * self.TILE_SIZE
        
        # Y-flip: row 0 should be at top (v=1.0), row 15 at bottom (v=0.0)
        v_max = 1.0 - (row * self.TILE_SIZE)
        v_min = 1.0 - ((row + 1) * self.TILE_SIZE)
        
        # Return UVs for quad vertices in standard order
        # This matches the vertex order used in World.create_chunk
        return [
            Vec2(u_min, v_min),  # Bottom-left
            Vec2(u_max, v_min),  # Bottom-right
            Vec2(u_max, v_max),  # Top-right
            Vec2(u_min, v_max),  # Top-left
        ]
    
    def get_tile_coords(self, tile_index: int) -> tuple[int, int]:
        """Get row and column coordinates for a tile index.
        
        Args:
            tile_index: Tile index (0-255)
            
        Returns:
            Tuple of (row, col) in the 16x16 grid
            
        Raises:
            ValueError: If tile_index is out of range
        """
        if not (0 <= tile_index < 256):
            raise ValueError(f"Tile index {tile_index} out of range (0-255)")
        
        row = tile_index // self.GRID_SIZE
        col = tile_index % self.GRID_SIZE
        return (row, col)
