# Natural Structure Generation System

## Overview

Complete system for procedurally generating natural decorative features across all biomes. All structures use existing textures from the atlas and follow deterministic noise-based placement.

---

## Available Structure Types

### 🌲 **Trees** (`tree_generator.py`)

| Type | Height | Shape | Best For |
|------|--------|-------|----------|
| **Standard** | 4-6 blocks | Round canopy | Forest |
| **Oak** | 3-4 blocks | Wide, flat-topped | Plains, foothills |
| **Pine** | 6-8 blocks | Tall, conical | Mountains, foothills |
| **Dead** | 3-5 blocks | No leaves (trunk only) | Swamp, canyon |
| **Bush** | 1 block | Ground-level leaves (2x2) | Plains, forest edges |

**Blocks used:** `wood` (trunk), `leaves` (foliage)

---

### 🪨 **Boulders** (`rock_generator.py`)

#### BoulderGenerator

| Type | Size | Shape | Best For |
|------|------|-------|----------|
| **Small** | 1-2 blocks | Single stone | Rocky, scattered everywhere |
| **Medium** | 3x3x3 | Irregular blob | Rocky, foothills |
| **Large** | 4x4x4 | Overhanging | Mountains, rocky |
| **Cluster** | 2-4 small | Grouped rocks | Rocky, mountain |

**Blocks used:** `stone`, `cobblestone_mossy`, `andesite`, `granite`

#### RockFormationGenerator

| Type | Dimensions | Description | Best For |
|------|------------|-------------|----------|
| **Spire** | 1x1 base, 5-8 tall | Needle-like pillar | Mountains, canyon |
| **Outcrop** | 5x5x3 | Stepped shelf | Rocky, canyon |
| **Pillar** | 3x3 base, 3-5 tall | Thick column | Mountains, rocky |

**Blocks used:** `stone`, `andesite`, `granite`

---

### 🌿 **Vegetation** (`vegetation_generator.py`)

#### VegetationGenerator

| Type | Size | Description | Best For |
|------|------|-------------|----------|
| **Tall Grass** | 1x1x1-2 | Single leaf column | Plains, forest, swamp |
| **Flower Patch** | 2-3 blocks | Small cluster | Plains, forest |
| **Mushrooms** | 2x2 area | Wood stems + leaf caps | Forest, swamp |
| **Ferns** | 2x2x2 | Spreading leaves | Forest, swamp |

**Blocks used:** `leaves` (grass/flowers/ferns), `wood` (mushroom stems)

#### FallenLogGenerator

| Type | Size | Description |
|------|------|-------------|
| **Fallen Log** | 3-6 blocks long | Horizontal wood line, follows terrain |

**Blocks used:** `wood`, occasional `leaves` (moss)

---

### 🌵 **Desert Features** (`desert_generator.py`)

#### CactusGenerator

| Type | Height | Description |
|------|--------|-------------|
| **Simple** | 2-4 blocks | Straight column |
| **Branched** | 3-5 + arms | Side branches with upward extensions |
| **Tall** | 5-7 blocks | Towering column |

**Blocks used:** `wood` (placeholder - could use dedicated cactus block)

#### DeadBushGenerator

Small dried vegetation (1-2 `wood` blocks)

#### SandDuneAccentGenerator

Sandstone/red sandstone outcrops (2x2 or 3x3, 1-2 blocks tall)

---

## Biome Structure Assignments

| Biome | Primary Structures | Density Notes |
|-------|-------------------|---------------|
| **Forest** | Standard/oak trees, grass, ferns, flowers, mushrooms, fallen logs | Dense (8% trees, 20% grass) |
| **Plains** | Sparse oak trees, bushes, lots of grass, flower patches | Moderate grass, sparse trees |
| **Rocky** | Boulders (all sizes), pillars | Boulder-heavy |
| **Mountain** | Pine trees (sparse), spires, outcrops, large boulders | Dramatic formations |
| **Desert** | Cacti, dead bushes, sandstone outcrops | Sparse, arid |
| **Canyon** | Spires, small boulders, dead bushes | Rock formations on mesas |
| **Swamp** | Dead trees, mushrooms, tall grass | Murky, fungal |
| **Foothill** | Mixed standard/pine trees, small boulders, grass | Transition zone |
| **Beach** | Minimal (dead bushes only) | Clean, open |
| **River** | None | Water feature |

See [`biome_structures.py`](file:///home/jamest/Desktop/dev/mycraft/games/voxel_world/structures/biome_structures.py) for exact density/scale values.

---

## Architecture

### Structure Generation Pipeline

```
1. Chunk Generation Start
   └─> Generate heightmap & biome data
   
2. Create Voxel Grid
   └─> Place terrain blocks (surface, subsurface)
   
3. Structure Placement
   ├─> Query biome structure config
   ├─> For each structure type:
   │   ├─> Noise check: should spawn at (x, z)?
   │   ├─> Validate terrain (flat enough?)
   │   ├─> Generate structure blocks
   │   └─> Add to voxel grid
   └─> Repeat for all positions
   
4. Build Mesh
   └─> Greedy meshing from voxel grid
   
5. Add Water & Collision (existing)
```

### Key Design Principles

✅ **Deterministic** - Same seed always generates same world  
✅ **Noise-based** - Natural clustering and distribution  
✅ **Biome-aware** - Each biome has appropriate structures  
✅ **Cross-chunk capable** - Structures can span boundaries  
✅ **Validation** - Prevents floating trees, buried boulders  
✅ **Extensible** - Easy to add new structure types  

---

## Integration Requirements

To integrate with [`world_gen.py`](file:///home/jamest/Desktop/dev/mycraft/games/voxel_world/systems/world_gen.py):

### Changes Needed

1. **Add voxel grid intermediate** - Store blocks before meshing
2. **Call structure generators** - After terrain, before meshing
3. **Update mesh builder** - Read from voxel grid instead of heightmap
4. **Pass height callback** - Allow structures to query terrain

### Integration Points

- `TerrainSystem.__init__()` - Store world seed
- `TerrainSystem.create_chunk()` - Add structure generation step
- `MeshBuilder` - Support voxel grid input (or convert heightmap logic)

See [`INTEGRATION_EXAMPLE.py`](file:///home/jamest/Desktop/dev/mycraft/games/voxel_world/structures/INTEGRATION_EXAMPLE.py) for conceptual implementation.

---

## Performance Considerations

| Factor | Impact | Mitigation |
|--------|--------|------------|
| Structure density | High densities increase chunk gen time | Tune density per biome (0.02-0.15) |
| Spacing parameter | Lower = more checks = slower | Use 2-5 block spacing |
| Structure complexity | Large structures = more blocks | Most structures < 100 blocks |
| Cross-chunk queries | Height callbacks across chunks | Cached heightmap per chunk |

**Estimated overhead:** ~10-30ms per chunk (depending on density)

---

## Future Enhancements

- **Ore veins** - Underground mineral deposits
- **Cave decorations** - Stalactites, crystals
- **Seasonal variants** - Snow-capped trees in winter
- **Biome transitions** - Blend structures at borders
- **Custom blocks** - Dedicated cactus, flower block types
- **Structure varieties** - More tree shapes, rock types

---

## Block Registry Dependencies

All structures use blocks from [`blocks.py`](file:///home/jamest/Desktop/dev/mycraft/games/voxel_world/blocks/blocks.py):

- ✅ `leaves` - **NEWLY REGISTERED** for foliage
- ✅ `wood` - Logs, cacti, dead trees
- ✅ `stone` - Base boulder type
- ✅ `cobblestone_mossy` - Boulder variation
- ✅ `andesite`, `granite` - Rock formation variety
- ✅ `sandstone`, `red_sandstone` - Desert accents

All textures available in atlas [`terrain.png`](file:///home/jamest/Desktop/dev/mycraft/docs/texture_atlas_reference.md).
