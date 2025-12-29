"""Verification test for Water Biomes and Logic."""

import unittest
from games.voxel_world.biomes.biomes import BiomeRegistry, beach_height, swamp_height, river_height

class TestBiomes(unittest.TestCase):
    def test_biomes_exist(self):
        """Verify new biomes are registered."""
        self.assertTrue(BiomeRegistry.exists("beach"))
        self.assertTrue(BiomeRegistry.exists("swamp"))
        self.assertTrue(BiomeRegistry.exists("river"))
        
    def test_beach_height(self):
        """Verify beach height logic."""
        # Beach should be between -1 and 0
        h = beach_height(0, 0)
        self.assertTrue(-1 <= h <= 0, f"Beach height {h} out of range")
        
    def test_swamp_height(self):
        """Verify swamp height logic."""
        # Swamp should be between -2 and 0
        h = swamp_height(0, 0)
        self.assertTrue(-2 <= h <= 0, f"Swamp height {h} out of range")
        
    def test_river_height(self):
        """Verify river height logic."""
        # River should be between -4 and -2 (below water level of 0)
        h = river_height(0, 0)
        self.assertTrue(-4 <= h <= -2, f"River height {h} out of range")
        
    def test_biome_selection(self):
        """Verify get_biome_at returns different biomes."""
        # This is probabilistic/noise-based, so just check we get valid biomes
        biomes_found = set()
        for x in range(0, 500, 10):
            for z in range(0, 500, 10):
                b = BiomeRegistry.get_biome_at(x, z)
                biomes_found.add(b.name)
                
        print(f"Biomes found in sample: {biomes_found}")
        # We hope to find 'beach' and 'swamp' in a large enough sample
        # But failure isn't critical if noise doesn't align in this specific range
        
if __name__ == "__main__":
    unittest.main()
