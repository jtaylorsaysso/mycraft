"""
Abstract protocol for chunk generation.

Games implement ChunkGenerator to define their terrain generation logic,
then pass it to ChunkManager for streaming and rendering.
"""

from typing import Protocol, Dict, Tuple, Any, Callable


class ChunkGenerator(Protocol):
    """Protocol defining the contract for chunk generation.
    
    Games implement this to specify how terrain is generated.
    The engine's ChunkManager calls these methods during chunk streaming.
    """
    
    def generate_chunk(
        self, 
        chunk_x: int, 
        chunk_z: int,
        chunk_size: int
    ) -> Dict[Tuple[int, int, int], str]:
        """Generate voxel grid for a chunk.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            chunk_size: Size of chunk in blocks (e.g., 16)
            
        Returns:
            Dict mapping (local_x, y, local_z) -> block_name
            Coordinates are chunk-local (0 to chunk_size-1 for x/z)
        """
        ...
    
    def get_height(self, x: float, z: float) -> float:
        """Get terrain height at world position.
        
        Used by physics, navigation, and cross-chunk queries.
        
        Args:
            x: World X coordinate
            z: World Z coordinate
            
        Returns:
            Height (Y coordinate) at this position
        """
        ...
    
    def get_block_registry(self) -> Any:
        """Get the block registry for block property lookups.
        
        Returns:
            Block registry with get_block(name) method
        """
        ...
