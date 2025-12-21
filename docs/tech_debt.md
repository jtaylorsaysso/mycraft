# Tech Debt

## World Generation

- [x] ~~World generation is currently a placeholder~~ - Now uses proper sine-wave based height function with greedy meshing
- [ ] World generation uses simple sine waves - should be enhanced with proper noise (Perlin/Simplex) for more varied terrain
- [x] ~~Only generates 3x3 chunk grid - needs dynamic chunk loading/unloading for larger worlds~~ - Implemented with configurable radius and throttling
- [x] ~~UV coordinates are basic (0,0 to 1,1 per quad) - textures stretch across merged quads from greedy meshing~~ - Resolved by disabling greedy meshing for top faces (now 1:1 mapping)
- [x] ~~Texture atlas system needed for varied block types~~ - Implemented with 16x16 grid (terrain.png) and per-face UV mapping
- [ ] Texture indexing appears incorrect - verify TileRegistry indices against actual atlas layout
- [x] ~~No biome system~~ - 6 biomes: Plains, Forest, Rocky, Desert, Mountain, Canyon with unique height functions

## Physics System

- [x] ~~Basic raycast ground detection~~ - Implemented with configurable parameters (hot-config enabled)
- [x] ~~Coyote time and jump buffering~~ - Implemented (0.2s windows)
- [x] ~~Variable jump height~~ - Implemented (early release = 55% velocity)
- [x] ~~Player floating above terrain after jumping~~ - Fixed by tuning raycast parameters (max_distance: 5.0, ray_origin_offset: 2.0)
- [ ] Add horizontal acceleration and deceleration for smoother movement
- [x] ~~Implement air control (limited horizontal movement while airborne)~~ - Implemented with 0.5 multiplier and 0.2 air friction
- [ ] Add slope handling and surface normal projection for angled terrain
- [x] ~~Wall collision detection~~ - Basic raycast wall check implemented in `physics.py`
- [x] ~~Improve wall sliding to allow smooth movement along walls~~ - Enhanced with momentum preservation (0.5x sliding)
- [x] ~~Collision parameters hardcoded~~ - Now tunable via hot-config (raycast_max_distance, raycast_origin_offset, foot_offset, hitbox dimensions)
- [x] ~~No collision debug visualization~~ - Implemented in `collision_debug.py` with F3 toggle and `/debug collision` command
- [ ] Consider different ground checks for liquids, ladders, etc.
- [ ] Add sliding on steep slopes

## Performance

- [x] ~~Greedy meshing for terrain~~ - Implemented for top faces, reduces vertex count significantly
- [ ] Profile raycast ground detection performance with many entities (NPCs, projectiles)
- [ ] Consider spatial partitioning for large numbers of physics objects
- [ ] Side face meshing is non-greedy - could be optimized further
- [ ] No LOD system for distant chunks
- [ ] Aggressive frustum culling disabled - incorrectly hid chunks at spawn; needs robust implementation with camera forward vector checks

## Networking

- [x] ~~Basic TCP client/server~~ - Implemented with asyncio
- [x] ~~Position synchronization~~ - Players send updates at 10Hz
- [x] ~~Remote player rendering~~ - Simple cube representation
- [x] ~~Admin console system~~ - Basic slash commands implemented
- [x] ~~Add player interpolation/extrapolation for smoother remote movement~~ - Implemented in `RemotePlayer` class with lerp
- [ ] Implement player names/labels above heads
- [ ] Add chat system for player communication (currently only admin console)
- [x] ~~Improve remote player visuals~~ - Remote players now use 5-part mannequin model matching local player
- [ ] Consider UDP for position updates (TCP for important events) - currently all TCP
- [ ] Add connection timeout and retry logic
- [ ] Implement player customization (colors, names, skins)
- [ ] Add bandwidth optimization (delta compression, interest management)

## Camera System

- [x] ~~Third-person over-the-shoulder camera~~ - Implemented with offset and look-ahead
- [x] ~~Camera collision detection~~ - Raycasts to prevent clipping through terrain
- [x] ~~Camera smoothing/damping for less jerky movement~~ - Lerp-based smoothing with 0.15 factor (hot-config)
- [ ] Camera bob/sway for more organic feel when walking/running
- [ ] Adjustable camera distance (zoom in/out)
- [ ] Camera occlusion handling when blocked by objects (fade out or move closer)

## Visual Polish

- [ ] Player model is basic stacked cubes - needs proper character model
- [x] ~~Remote players render as single cubes~~ - Now use 5-part mannequin matching local player
- [x] ~~No animations (walking, jumping, landing, idle)~~ - Procedural animations implemented with AnimatedMannequin and AnimationController
- [ ] No particle effects (dust clouds, jump/land impacts)
- [ ] Basic static lighting - needs dynamic lighting and shadows
- [x] ~~Single texture for all terrain~~ - Texture atlas with 18 block types and per-face tiles
- [ ] No skybox or atmosphere rendering

## Input Handling

- [x] ~~Basic WASD movement~~ - Implemented
- [x] ~~Mouse look~~ - Implemented with camera pivot
- [x] ~~Space to jump~~ - Implemented with buffering
- [ ] No key rebinding / customization
- [ ] No gamepad/controller support
- [x] ~~Mouse sensitivity not configurable~~ - Hot-config enabled via playtest.json
- [ ] No mouse smoothing options

## Testing & Quality

- [x] ~~Basic physics tests~~ - Present in `tests/` directory
- [x] ~~Server admin tests~~ - Present in `tests/` directory
- [x] ~~No automated integration tests for multiplayer scenarios~~ - Implemented in `tests/`
- [ ] No performance benchmarks or regression tests
- [ ] No CI/CD pipeline
- [ ] Limited error handling in network code
- [ ] No client-side prediction or lag compensation testing

## Post-Refactor Cleanup

- [ ] `engine/systems/network.py`: Implement server replication logic (TODO)
- [ ] `engine/systems/interaction.py`: Implement stacking logic (TODO)
- [x] ~~`engine/systems/interaction.py`: Spawn item entity at position~~ - Implemented via event dispatch
- [ ] `tests/benchmarks/test_chunk_generation.py`: Refactor for better benchmarking (TODO)
- [ ] Evaluate need for `shared/` directory (removed as it was empty)

## Ursina Migration Progress (Dec 2024)

### ✅ Completed - Migration 100% Done

- [x] Engine layer fully migrated to Panda3D (config_loader.py)
- [x] All engine tests use Panda3D vectors
- [x] Unified input system (PlayerControlSystem + GameplayInputSystem)
- [x] Legacy InputHandler deprecated
- [x] Inventory drop functionality via ECS events
- [x] **Animation system migrated** (AnimatedMannequin → Panda3D NodePath)
- [x] **HUD system migrated** (Ursina Text/Entity → Panda3D OnscreenText)
- [x] **Remote player rendering migrated** (Ursina Entity → Panda3D NodePath)
- [x] **Removed Ursina from requirements.txt**
- [x] **Deprecated files removed** (entities/, components/, ui/, systems/ from games/voxel_world/)

### 📊 Final Status

**Zero active Ursina imports in project code!**

All deprecated code has been removed. The codebase is now 100% Panda3D native.

### 🎯 Next Steps (Sprint 4: System Completeness) ✅ COMPLETE

- [x] **Server replication** - Component sync system with 20Hz broadcast
- [x] **Inventory stacking** - Smart stacking with (item_type, count) tuples
- [x] **Noise-based terrain generation** - Perlin noise for all biomes
- [x] **Player name labels** - 3D billboarded TextNode tags

### 📋 Sprint 5: Polish & UX (Next)

**Physics Improvements:**

- [ ] Horizontal acceleration and deceleration for smoother movement
- [ ] Slope handling and surface normal projection
- [ ] Liquid detection for proper water physics integration

**Camera Enhancements:**

- [ ] Camera bob during movement
- [ ] Zoom functionality (scroll wheel)
- [ ] Camera occlusion handling (fade walls)

**Networking:**

- [ ] Client timeout handling (already in server, needs client-side)
- [ ] Connection customization (quality settings)
- [ ] Network optimization (delta compression, priority)

**Visual Effects:**

- [ ] Particle system foundation
- [ ] Block break particles
- [ ] Water splash effects
