
# Baseline Performance Metrics

**Date:** 2025-12-14
**Hardware:** linux (x86_64), Python 3.12.3

## Summary

This document records the baseline performance of core engine subsystems. These benchmarks are micro-benchmarks targeting specific logic paths using `pytest-benchmark`.

### Results

| Benchmark | Mean (s) | Min (s) | Max (s) | OPS | Description |
|---|---|---|---|---|---|
| `test_chunk_generation_benchmark` | 0.000001 | 0.000001 | 0.000023 | 940,179 | Biome registry lookup speed |
| `test_height_map_benchmark` | 0.000004 | 0.000002 | 0.007049 | 281,263 | Height calculation logic |
| `test_get_tile_uvs_benchmark` | 0.000002 | 0.000002 | 0.000034 | 426,062 | Single tile UV calculation |
| `test_get_tiled_uvs_benchmark` | 0.000002 | 0.000002 | 0.000025 | 522,763 | Merged quad (greedy mesh) UVs |
| `test_message_serialization` | 0.000028 | 0.000019 | 0.004792 | 35,869 | JSON dump of 16-player state |
| `test_message_deserialization` | 0.000021 | 0.000015 | 0.000086 | 48,116 | JSON load of 16-player state |
| `test_physics_update_benchmark` | 0.000001 | 0.000001 | 0.000006 | 1,186,479 | Kinematic update (no collision) |
| `test_gravity_integration` | 0.000000 | 0.000000 | 0.000002 | 4,137,184 | Gravity math calc |

## Analysis

### Chunk Generation
The current benchmark tests `BiomeRegistry.get_biome_at` and `World.get_height`. These are extremely fast (>200k OPS), indicating the bottleneck in actual chunk generation is likely the `Ursina.Entity` instantiation and mesh generation, not the procedural generation logic.

### Meshing
Texture Atlas UV calculations are efficient (~2µs per operation). A full chunk (256 blocks) surface calculation would be negligible. The bottleneck is likely memory allocation during mesh construction.

### Networking
Serialization of a standard 16-player snapshot takes ~28µs. This supports a theoretical tick rate far exceeding the target 60Hz.

### Physics
Physics math is trivial (~1µs). The real cost will be in `raycast` queries which were mocked in these micro-benchmarks. Future benchmarks should include live raycasts against geometry.

## Methodology

Benchmarks were run using:
```bash
python -m pytest tests/benchmarks/ --benchmark-only --benchmark-json=baseline.json
```
