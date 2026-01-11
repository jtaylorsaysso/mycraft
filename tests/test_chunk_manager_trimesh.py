
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.world.chunk_manager import ChunkManager

class TestChunkManagerTrimesh(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_world = MagicMock()
        self.mock_event_bus = MagicMock()
        self.mock_base = MagicMock()
        self.mock_generator = MagicMock()
        
        # Setup mock base render
        self.mock_base.render = MagicMock()
        self.mock_base.render.attachNewNode.return_value = MagicMock()
        
        # Setup mock generator
        # Return empty entities/loot for simplicity
        self.mock_generator.generate_chunk.return_value = ({
            (0, 0, 0): 'dirt',
            (1, 0, 0): 'stone'
        }, [], {})
        
        # Setup block registry mock
        mock_block_def = MagicMock()
        mock_block_def.solid = True
        self.mock_registry = MagicMock()
        self.mock_registry.get_block.return_value = mock_block_def
        self.mock_generator.get_block_registry.return_value = self.mock_registry
        
        # Create manager
        self.manager = ChunkManager(
            world=self.mock_world,
            event_bus=self.mock_event_bus,
            base=self.mock_base,
            generator=self.mock_generator,
            chunk_size=16
        )

    def test_trimesh_cache_lifecycle(self):
        """Test that trimesh objects are cached on creation and removed on unload."""
        # Ensure trimesh is available (should be since we installed it)
        if not self.manager.has_trimesh:
            self.skipTest("Trimesh not available")
            
        # 1. Create chunk
        chunk_x, chunk_z = 0, 0
        self.manager.create_chunk(chunk_x, chunk_z)
        
        # 2. Verify mesh is cached
        self.assertIn((chunk_x, chunk_z), self.manager.chunk_meshes)
        cached_mesh = self.manager.chunk_meshes[(chunk_x, chunk_z)]
        
        # Verify it's a trimesh object (by checking attribute)
        self.assertTrue(hasattr(cached_mesh, 'vertices'))
        self.assertTrue(hasattr(cached_mesh, 'faces'))
        
        # 3. Verify get_terrain_mesh works
        combined = self.manager.get_terrain_mesh()
        self.assertIsNotNone(combined)
        self.assertEqual(len(combined.vertices), len(cached_mesh.vertices))
        
        # 4. Unload chunk
        self.manager.unload_chunk(chunk_x, chunk_z)
        
        # 5. Verify mesh is removed
        self.assertNotIn((chunk_x, chunk_z), self.manager.chunk_meshes)
        
        # 6. Verify get_terrain_mesh returns None or empty
        combined_after = self.manager.get_terrain_mesh()
        self.assertIsNone(combined_after)

if __name__ == '__main__':
    unittest.main()
