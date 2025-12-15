
from engine.world import World
from engine.blocks import Block
from engine.biomes import BiomeRegistry

# ... (mock setup) ...

def test_chunk_generation_benchmark(benchmark):
    """Benchmark full chunk generation including blocks."""
    
    # Setup
    world = World()  # Removed seed arg
    # ...
    
    def biome_calc():
        return BiomeRegistry.get_biome_at(100, 100)
    
    result = benchmark(biome_calc)
    assert result is not None

def test_height_map_benchmark(benchmark):
    """Benchmark height calculation."""
    world = World() # Removed seed arg
    
    def get_height():
        return world.get_height(50, 50) # get_height_at -> get_height
        
    benchmark(get_height)

# Note: Ideally we would benchmark `generate_chunk_data` but that method doesn't exist separately yet.
# Adding a TODO to refactor for better benchmarking.
