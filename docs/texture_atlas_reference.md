# Texture Atlas Reference

## Overview

The MyCraft texture atlas system uses a single 256×256 pixel texture (`Spritesheets/terrain.png`) organized as a **16×16 grid** of 16×16 pixel tiles, indexed 0–255 in row-major order.

**Implementation:** [`engine/rendering/texture_atlas.py`](file:///home/jamest/Desktop/dev/mycraft/engine/rendering/texture_atlas.py)

## Atlas Specifications

| Property | Value |
|----------|-------|
| **Atlas Size** | 256 × 256 pixels |
| **Grid Layout** | 16 × 16 tiles |
| **Tile Size** | 16 × 16 pixels |
| **Total Tiles** | 256 (indexed 0–255) |
| **Filtering** | Nearest-neighbor (pixel-perfect) |
| **Wrapping** | Repeat on U/V axes |

## Registered Tile Indices

The `TileRegistry` class defines the following tile mappings:

### Natural Terrain

| Index | Constant | Description | Used By |
|-------|----------|-------------|---------|
| **0** | `GRASS_TOP` | Grass block top face | grass (top) |
| **2** | `DIRT` | Brown dirt | grass (bottom), dirt (all), snow (bottom), podzol (bottom), mud (all) |
| **3** | `GRASS_SIDE` | Grass side (green top, dirt below) | grass (side) |
| **14** | `DIRT_PODZOL` | Dark forest floor dirt | podzol (top/side) |
| **18** | `SAND` | Yellow sand | sand (all), beach, river |
| **19** | `GRAVEL` | Gravel texture | gravel (all), river (subsurface) |
| **66** | `SNOW` | Snow top surface | snow (top) |
| **68** | `SNOW_SIDE` | Snow-topped grass side | snow (side) |
| **72** | `CLAY` | Clay block | clay (all) |

### Stone & Rock

| Index | Constant | Description | Used By |
|-------|----------|-------------|---------|
| **1** | `STONE` | Standard grey stone | stone (all), mountain |
| **6** | `STONE_ANDESITE` | Andesite stone variation | andesite (all) |
| **16** | `COBBLESTONE` | Cobblestone | *registered but unused* |
| **17** | `BEDROCK` | Bedrock (bottom layer) | *registered but unused* |
| **36** | `COBBLESTONE_MOSSY` | Mossy cobblestone | cobblestone_mossy (all), rocky (subsurface) |
| **48** | `STONE_MOSSY` | Mossy stone | stone_mossy (all) |
| **213** | `STONE_GRANITE` | Granite variation | granite (all) |

### Desert & Mesa

| Index | Constant | Description | Used By |
|-------|----------|-------------|---------|
| **159** | `CLAY_TERRACOTTA` | Terracotta (mesa layering) | terracotta (all), canyon (subsurface) |
| **179** | `RED_SANDSTONE` | Red sandstone | red_sandstone (all) |
| **192** | `SANDSTONE` | Standard sandstone | sandstone (all), desert (subsurface), beach (subsurface) |
| **209** | `RED_SAND` | Red sand (canyon biome) | red_sand (all), canyon |

### Wood & Vegetation

| Index | Constant | Description | Used By |
|-------|----------|-------------|---------|
| **4** | `WOOD_PLANKS` | Wooden planks | *registered but unused* |
| **20** | `LOG_SIDE` | Wood log bark | wood (side) |
| **21** | `LOG_TOP` | Wood log cross-section | wood (top/bottom) |
| **52** | `LEAVES` | Tree leaves | *registered but unused* |

### Ice & Snow

| Index | Constant | Description | Used By |
|-------|----------|-------------|---------|
| **67** | `ICE` | Standard ice | *registered but unused* |
| **165** | `ICE_PACKED` | Packed ice | ice (all) |

### Crafted Blocks

| Index | Constant | Description | Used By |
|-------|----------|-------------|---------|
| **7** | `BRICK` | Brick block | *registered but unused* |
| **8** | `TNT_SIDE` | TNT side texture | *registered but unused* |
| **9** | `TNT_TOP` | TNT top texture | *registered but unused* |
| **10** | `TNT_BOTTOM` | TNT bottom texture | *registered but unused* |
| **35** | `BOOKSHELF` | Bookshelf block | *registered but unused* |

### Liquids

| Index | Constant | Description | Used By |
|-------|----------|-------------|---------|
| **205** | `WATER` | Water texture | *registered, water mesh uses solid color* |
| **237** | `LAVA` | Lava texture | *registered but unused* |

## Block Type Mappings

Each block type can use different tiles for its **top**, **side**, and **bottom** faces:

```python
# Example: Grass block
Block(
    name="grass",
    tile_top=0,      # GRASS_TOP
    tile_side=3,     # GRASS_SIDE
    tile_bottom=2    # DIRT
)
```

### Complete Block-to-Tile Mapping

| Block Name | Top | Side | Bottom | Biome Usage |
|------------|-----|------|--------|-------------|
| `grass` | 0 | 3 | 2 | Plains, Forest |
| `dirt` | 2 | 2 | 2 | Subsurface (plains/forest) |
| `stone` | 1 | 1 | 1 | Rocky, Mountain |
| `sand` | 18 | 18 | 18 | Desert, Beach, River |
| `gravel` | 19 | 19 | 19 | River (subsurface) |
| `sandstone` | 192 | 192 | 192 | Desert/Beach (subsurface) |
| `red_sand` | 209 | 209 | 209 | Canyon |
| `terracotta` | 159 | 159 | 159 | Canyon (subsurface) |
| `cobblestone_mossy` | 36 | 36 | 36 | Rocky (subsurface) |
| `snow` | 66 | 68 | 2 | *(not used in biomes yet)* |
| `clay` | 72 | 72 | 72 | *(not used in biomes yet)* |
| `wood` | 21 | 20 | 21 | *(not used in biomes yet)* |
| `podzol` | 14 | 14 | 2 | *(not used in biomes yet)* |
| `ice` | 165 | 165 | 165 | *(not used in biomes yet)* |
| `stone_mossy` | 48 | 48 | 48 | *(not used in biomes yet)* |
| `andesite` | 6 | 6 | 6 | *(not used in biomes yet)* |
| `granite` | 213 | 213 | 213 | *(not used in biomes yet)* |
| `red_sandstone` | 179 | 179 | 179 | *(not used in biomes yet)* |
| `mud` | 2 | 2 | 2 | Swamp *(no unique texture)* |

## UV Coordinate System

The `TextureAtlas` class provides UV lookups for rendering:

```python
# Get UVs for a single tile
uvs = atlas.get_tile_uvs(tile_index)
# Returns: [bottom-left, bottom-right, top-right, top-left]

# Get UVs for a tiled/merged quad (greedy meshing)
uvs = atlas.get_tiled_uvs(tile_index, width=3, height=2)
# Texture repeats 3×2 times across the merged quad
```

**Coordinate System:**

- Origin: Bottom-left (OpenGL convention)
- Y-axis: Flipped (row 0 at top → v=1.0, row 15 at bottom → v=0.0)
- U range: [0.0, 1.0] (left to right)
- V range: [0.0, 1.0] (bottom to top)

## Unused Textures (Opportunities)

The following textures are registered but **not currently used** in world generation:

### High Priority

- **`LEAVES` (52)** — Forest biome could generate tree structures
- **`LOG_SIDE/TOP` (20, 21)** — `wood` block registered but unused
- **`WATER` (205)** — Water mesh currently uses solid blue color
- **`SNOW` (66, 68)** — Mountain peaks could use snow caps

### Medium Priority

- **`COBBLESTONE` (16)** — Could be rocky subsurface variation
- **`STONE_MOSSY/ANDESITE/GRANITE` (48, 6, 213)** — Rocky biome variety
- **`ICE` (67, 165)** — Tundra/frozen biome feature
- **`CLAY` (72)** — River banks or swamp feature

### Low Priority

- **`BRICK` (7)** — Ruins/structures
- **`TNT_*` (8-10)** — Player-placed explosives
- **`BOOKSHELF` (35)** — Interior decoration
- **`LAVA` (237)** — Volcanic biome or underground

## Extension Opportunities

1. **Height-based texturing** — Transition grass → stone at elevation, add snow caps
2. **Tree generation** — Use log/leaf blocks in forest biome
3. **Structure generation** — Ruins using brick, cobblestone, bookshelf
4. **New biomes** — Tundra (ice/snow), volcano (lava/basalt), swamp (mud with unique texture)
5. **Underground variety** — Bedrock base layer, ore pockets

---

*Last Updated: 2025-12-25*  
*Version: 1.0 — Initial Atlas Documentation*
