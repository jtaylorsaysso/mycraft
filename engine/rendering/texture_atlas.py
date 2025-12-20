"""Texture atlas system for efficient block rendering using Panda3D."""

from typing import Optional
from panda3d.core import Texture, LVector2f, Filename
from engine.core.logger import get_logger


class TextureAtlas:
    """Manages texture atlas loading and UV coordinate mapping.
    
    The atlas is a 256x256 image containing a 16x16 grid of 16x16 pixel tiles.
    Tiles are indexed 0-255 in row-major order from top-left.
    """
    
    GRID_SIZE = 16  # 16x16 tiles
    TILE_SIZE = 1.0 / GRID_SIZE  # Normalized tile size (1/16)
    
    def __init__(self, image_path: str, loader=None):
        """Initialize the texture atlas.
        
        Args:
            image_path: Path to the texture atlas image (e.g., "Spritesheets/terrain.png")
            loader: Panda3D loader instance (from ShowBase)
        """
        self.logger = get_logger("texture_atlas")
        self.image_path = image_path
        self._texture: Optional[Texture] = None
        
        # Try to load the texture using Panda3D
        if loader:
            try:
                self._texture = loader.loadTexture(Filename.fromOsSpecific(image_path))
                if self._texture:
                    # Configure texture settings for pixel art
                    self._texture.setMinfilter(Texture.FTNearest)
                    self._texture.setMagfilter(Texture.FTNearest)
                    self._texture.setWrapU(Texture.WMRepeat)
                    self._texture.setWrapV(Texture.WMRepeat)
                    self.logger.info(f"Loaded texture atlas from {image_path}")
                else:
                    self.logger.error(f"Failed to load texture atlas from {image_path}")
            except Exception as e:
                self.logger.error(f"Failed to load texture atlas from {image_path}: {e}")
                self._texture = None
        else:
            self.logger.warning("No loader provided, texture atlas will not be loaded")
    
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
    
    def get_tile_uvs(self, tile_index: int) -> list[LVector2f]:
        """Get UV coordinates for a tile as a quad (4 vertices).
        
        Args:
            tile_index: Tile index (0-255) in row-major order
            
        Returns:
            List of 4 LVector2f UV coordinates for quad vertices in order:
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
        return [
            LVector2f(u_min, v_min),  # Bottom-left
            LVector2f(u_max, v_min),  # Bottom-right
            LVector2f(u_max, v_max),  # Top-right
            LVector2f(u_min, v_max),  # Top-left
        ]
    
    def get_tiled_uvs(self, tile_index: int, width: int = 1, height: int = 1) -> list[LVector2f]:
        """Get UV coordinates for a tiled quad (texture repeats across merged blocks).
        
        For greedy meshing: when multiple same-height blocks are merged into one quad,
        the texture should tile/repeat rather than stretch. This method scales the UV
        coordinates so the texture repeats width×height times.
        
        Args:
            tile_index: Tile index (0-255) in row-major order
            width: Number of blocks in the X direction (quad width in blocks)
            height: Number of blocks in the Z direction (quad depth in blocks)
            
        Returns:
            List of 4 LVector2f UV coordinates for quad vertices in order:
            [bottom-left, bottom-right, top-right, top-left]
            
        Raises:
            ValueError: If tile_index is out of range
        """
        if not (0 <= tile_index < 256):
            raise ValueError(f"Tile index {tile_index} out of range (0-255)")
        
        # Calculate row and column from tile index
        row = tile_index // self.GRID_SIZE
        col = tile_index % self.GRID_SIZE
        
        # Base UV coordinates for this tile in the atlas
        u_base = col * self.TILE_SIZE
        v_base = 1.0 - ((row + 1) * self.TILE_SIZE)  # Y-flipped
        
        # Scale UVs by width/height so the tile repeats across the merged quad
        u_extent = width * self.TILE_SIZE
        v_extent = height * self.TILE_SIZE
        
        return [
            LVector2f(u_base, v_base),                         # Bottom-left
            LVector2f(u_base + u_extent, v_base),              # Bottom-right
            LVector2f(u_base + u_extent, v_base + v_extent),   # Top-right
            LVector2f(u_base, v_base + v_extent),              # Top-left
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


class TileRegistry:
    """Registry of standard tile indices from the texture atlas.
    
    Indices correspond to the 16x16 grid in terrain.png (0-255).
    """
    
    # Grass/Dirt
    GRASS_TOP = 0
    GRASS_SIDE = 3
    DIRT = 2
    
    # Stone/Ores
    STONE = 1
    COBBLESTONE = 16
    BEDROCK = 17
    
    # Nature
    WOOD_PLANKS = 4
    LOG_SIDE = 20
    LOG_TOP = 21
    LEAVES = 52
    
    # Environment
    SAND = 18
    GRAVEL = 19
    SNOW = 66
    SNOW_SIDE = 68
    ICE = 67
    
    # Resources
    CLAY = 72
    WATER = 205
    LAVA = 237
    
    # Crafted
    BRICK = 7
    TNT_SIDE = 8
    TNT_TOP = 9
    TNT_BOTTOM = 10
    BOOKSHELF = 35
    
    # Natural Terrain Variations
    COBBLESTONE_MOSSY = 36
    DIRT_PODZOL = 14
    SANDSTONE = 192
    
    # Mountain/Snow Terrain
    STONE_MOSSY = 48
    ICE_PACKED = 165
    
    # Canyon/Mesa Terrain
    RED_SAND = 209
    CLAY_TERRACOTTA = 159
    RED_SANDSTONE = 179
    
    # Rock Variations
    STONE_ANDESITE = 6
    STONE_GRANITE = 213
    
    @classmethod
    def get(cls, name: str) -> int:
        """Get a tile index by name (case-insensitive)."""
        name = name.upper()
        if hasattr(cls, name):
            return getattr(cls, name)
        raise ValueError(f"Unknown tile name: {name}")
