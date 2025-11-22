# World Generation Guidelines (Action-RPG Oriented)

## 1. Coordinate & Chunk Basics

- **Ground Level**
  - `y = 0` is the **ground level**.
  - All walkable terrain should have its *top* surface at or near `y = 0`.
  - Baseline: no gameplay-relevant terrain below `y = 0`.

- **Vertical Depth**
  - Maximum depth: **1 chunk deep**.
  - For this baseline implementation:
    - Terrain is a thin shell: mostly a single layer at `y = 0`.
    - Optional extra blocks below (e.g. `y = -1`) may be used for visual support, but not for gameplay.

- **Chunks**
  - Default **chunk size**: `16 × 16` in `(x, z)`.
  - Chunks are **technical/structural units** (for performance and streaming), not gameplay units.
  - Design world content "by chunk" (encounter areas, paths, vistas), but do not expose chunk structure directly to the player.

## 2. Terrain & Layout Philosophy (Action-RPG)

- **Level-like, Not Sandbox**
  - World generation should favor **readable combat and exploration spaces**, not open-ended mining.
  - Priorities:
    - Clear **paths**, **arenas**, **plazas**, **villages**, and **landmarks**.
    - Controlled sight lines (for ranged combat, ambushes, vistas).

- **Height Usage**
  - Avoid noisy, highly fractal terrain.
  - Prefer:
    - Gentle slopes and plateaus around `y = 0`.
    - Occasional cliffs or steps (1–3 blocks) to gate areas or create vantage points.
  - Because we are only one chunk deep, treat terrain as a **surface** rather than a volume (no deep caves/mines in this baseline).

- **Block Permanence**
  - Baseline assumption: **no block destruction or placement by the player**.
    - Terrain is static geometry.
    - Encounters and navigation should *not* rely on digging or building.
  - This simplifies:
    - Physics and collision.
    - Chunk meshes (rarely or never rebuilt at runtime).

## 3. World Generation Responsibilities

- **Generator Goals**
  - Produce **static terrain chunks** with:
    - Walkable surfaces at or near `y = 0`.
    - Local variation that supports combat and exploration (hills, plateaus, small cliffs).
  - Avoid generating:
    - Deep vertical stacks of blocks.
    - Cave networks or extensive underground spaces.
    - Excessive high-frequency noise that makes movement frustrating.

- **Per-Chunk Design Hooks**
  - Each chunk may have a **type** (e.g. plains, forest, canyon, settlement, dungeon entrance).
  - Chunks can carry **metadata** (e.g. encounter difficulty, story beats, spawn tables).
  - The generation system must allow:
    - Procedural generation by type.
    - Optional overrides with handcrafted layouts.
    - A blend of authored and procedural content.

## 4. Physics & Navigation Assumptions

- **Physics Baseline**
  - Blocks are axis-aligned solid colliders.
  - Player movement:
    - Runs and stands on top surfaces around `y = 0`.
    - Cannot dig through or build on terrain at this baseline.

- **Navigation**
  - With shallow vertical depth, navigation can be treated as mostly **2D (x, z)** with height checks.
  - Local height differences define:
    - Walkable vs non-walkable tiles.
    - Step-up / step-down thresholds (for jumping or climbing in future mechanics).

## 5. Implementation Guidelines

- **Height Function API**
  - Provide a function such as `get_height(x, z)` that:
    - Returns an integer `y` height.
    - Respects the `y = 0` ground baseline (no excessively deep pits).
    - Favors broad shapes over detailed noise.

- **Chunk Creation**
  - `create_chunk(chunk_x, chunk_z)` should:
    - Use `get_height` (or similar) to determine terrain per column.
    - Generate static geometry once when the chunk is created.
    - Store a reference to the chunk entity/mesh in a chunk map for future streaming or culling.

- **Meshing Focus**
  - Optimize for **static meshes per chunk**:
    - Combine blocks into one or a few meshes per chunk.
    - Expect rare or no runtime mesh rebuilds since blocks are not destroyed.

## 6. Current Implementation Status

### ✅ Implemented

- **Chunk System**: 16×16 blocks per chunk, 3×3 chunk grid
- **Height Function**: Gentle sine waves with y=0 baseline, ±2 block variation
- **Meshing**: Greedy meshing for top faces, side face culling based on height differences
- **Performance**: Single mesh per chunk with optimized vertex count

### 🔄 Current Design

- **Static Terrain**: No block destruction/placement baseline
- **Action-RPG Focus**: Readable combat spaces, gentle slopes
- **Ground Level**: y=0 as primary walkable surface

### 📋 Future Extensions
These are explicitly **out of scope** for the baseline but should be considered when extending the system:

- Player-driven block destruction/placement
- Multi-layer underground spaces and cave systems
- Dynamic terrain deformation (explosions, spells, etc.)
- Dynamic chunk loading/unloading for very large worlds

---

*Last Updated: 2025-11-22*
*Version: 1.0*
