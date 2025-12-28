# Tech Debt Register

**Last Updated:** 2025-12-27

This register tracks technical debt, bugs, and future enhancements. Items are organized by priority and aligned with the project's current development direction.

---

## 🔥 High Priority

### Camera System Issues

**Priority:** High | **Effort:** ~30 minutes

- [ ] **Scroll wheel zoom broken after 1st→3rd person toggle** - Zoom works initially but stops functioning after toggling camera modes. Likely state not being reset properly on mode switch.

### Coordinate System Test Issues  

**Priority:** High | **Effort:** ~1 hour

During controls polishing audit, found test files still using Ursina (Y-up) instead of Panda3D (Z-up):

- [ ] `tests/test_player_physics.py` - Lines 116, 120, 122, 145, 151 check `velocity_y` instead of `velocity_z`
- [ ] `tests/test_physics_raycast.py` - Uses `entity.y` for vertical position throughout
- [ ] `tests/test_physics_manual.py` - MockEntity uses Y for vertical (lines 13-17)
- [ ] `tests/benchmarks/test_physics.py` - Line 39 sets vertical velocity on wrong axis
- [ ] Clean up outdated "Ursina" references in test comments (6 files)

**Impact:** Tests provide false confidence - actual vertical physics coverage incomplete.  
**Reference:** `coordinate_audit.md` in artifacts directory

---

## 🎯 Medium Priority - Aligned with Current Direction

### State Management Architecture

**Priority:** Medium-High | **Effort:** ~1-2 weeks for remaining items

Remaining items from state management cleanup:

- [ ] **No hierarchical state machine** - `GameState` only tracks PLAYING/PAUSED/MENU. Future features (combat stances, dialogue, cutscenes) will need proper state machine with sub-states.
- [ ] **UI modal stack** - Individual overlay booleans (`pause_overlay.visible`, `chat_input_active`) instead of ordered stack for input priority
- [ ] **Manual dirty tracking** - `SyncSystem` manually tracks changed entities. Should use automatic component change detection (generation counters or dirty flags).

**Reference:** Full assessment in artifacts directory (`state_management_gap_assessment.md`)

### Physics & Collision  

**Priority:** Medium | **Effort:** Varies

- [ ] Profile raycast ground detection performance with many entities (NPCs, projectiles)
- [ ] Consider spatial partitioning for large numbers of physics objects

### World Generation

**Priority:** Medium | **Effort:** ~2-3 days

- [ ] World generation uses simple sine waves - should be enhanced with proper noise (Perlin/Simplex) for more varied terrain
- [ ] Texture indexing appears incorrect - verify TileRegistry indices against actual atlas layout

### Networking & Multiplayer

**Priority:** Medium | **Effort:** Varies

- [ ] Implement player names/labels above heads
- [ ] Add chat system for player communication (currently only admin console)
- [ ] Consider UDP for position updates (TCP for important events) - currently all TCP
- [ ] Add connection timeout and retry logic
- [ ] Implement player customization (colors, names, skins)
- [ ] Add bandwidth optimization (delta compression, interest management)

---

## 🔧 Quality of Life & Polish

### Visual Polish

**Priority:** Low-Medium | **Effort:** Varies

- [ ] Player model is basic stacked cubes - needs proper character model
- [ ] No particle effects (dust clouds, jump/land impacts)
- [ ] Basic static lighting - needs dynamic lighting and shadows
- [ ] No skybox or atmosphere rendering

### Input & Controls

**Priority:** Low | **Effort:** Varies

- [ ] No key rebinding / customization
- [ ] No gamepad/controller support
- [ ] No mouse smoothing options

### UI/UX Features (Deferred)

**Priority:** Low | **Effort:** ~1-2 weeks

- [ ] **Host-Only Debug Panel**: Network monitoring (ping, packet loss), Entity inspector, Performance profiler
- [ ] **In-Game Console**: Log viewer and command input overlay

---

## ⚡ Performance Optimization

**Priority:** Medium-Low | **Effort:** Varies

- [ ] Side face meshing is non-greedy - could be optimized further
- [ ] No LOD system for distant chunks
- [ ] Aggressive frustum culling disabled - incorrectly hid chunks at spawn; needs robust implementation with camera forward vector checks
- [ ] Separate client runner from main code?
- [ ] No performance benchmarks or regression tests
- [ ] No CI/CD pipeline

---

## 📝 Code Cleanup & TODOs

**Priority:** Low | **Effort:** ~1-2 days total

- [ ] `engine/systems/network.py`: Implement server replication logic (TODO)
- [ ] `engine/systems/interaction.py`: Implement stacking logic (TODO)
- [ ] `tests/benchmarks/test_chunk_generation.py`: Refactor for better benchmarking (TODO)
- [ ] Limited error handling in network code
- [ ] No client-side prediction or lag compensation testing

---

## ✅ Recently Completed (2025-12-27)

### State Management Cleanup

- [x] **KinematicState dict storage** - Converted to proper ECS component. Automated tests pass (9/9 physics tests)
- [x] **Input blocking fragility** - Replaced single boolean with blocking stack. Tests: 4/4 passed
- [x] **Cursor lock duplication** - Eliminated `VoxelGame._cursor_locked`, made `InputManager` single source of truth
- [x] **Per-frame allocations** - `PlayerContext` now created once and updated in-place
- [x] **Camera state fragmentation** - Unified into `CameraState` ECS component with `CameraMode` enum. Tests: 2/2 passed

### Camera Enhancements (Sprint 5)

- [x] Camera collision detection (raycasting)
- [x] Camera bob during movement (sine-wave oscillation)
- [x] Zoom functionality (scroll wheel)
- [x] Third-person over-the-shoulder camera with offset and look-ahead
- [x] Camera smoothing/damping with lerp-based smoothing (0.15 factor)

### Physics & Movement

- [x] Basic raycast ground detection with configurable parameters
- [x] Coyote time and jump buffering (0.2s windows)
- [x] Variable jump height (early release = 55% velocity)
- [x] Horizontal acceleration and deceleration
- [x] Air control (0.5 multiplier)
- [x] Slope handling with surface normal projection
- [x] Wall collision detection with momentum-based sliding
- [x] Collision debug visualization (F3 toggle)
- [x] Water physics integration with shared KinematicState
- [x] Side face collision geometry (2025-12-27) - Players can no longer phase through vertical walls

### World & Rendering

- [x] Greedy meshing for terrain (top faces)
- [x] Texture atlas system with 16x16 grid
- [x] UV coordinates fixed for proper texture mapping
- [x] 6 biomes: Plains, Forest, Rocky, Desert, Mountain, Canyon
- [x] Dynamic chunk loading/unloading with configurable radius

### Animations & Player Model

- [x] Procedural animations with AnimatedMannequin and AnimationController
- [x] Remote players use 5-part mannequin model matching local player

### Networking

- [x] Basic TCP client/server with asyncio
- [x] Position synchronization at 10Hz
- [x] Remote player rendering
- [x] Admin console system with slash commands
- [x] Player interpolation/extrapolation for smooth remote movement
- [x] Component sync system with 20Hz broadcast

### Input & Configuration

- [x] Mouse sensitivity configurable via hot-config
- [x] Collision parameters tunable via hot-config
- [x] Unified input system (PlayerControlSystem + GameplayInputSystem)

### Testing

- [x] Basic physics tests
- [x] Server admin tests
- [x] Automated integration tests for multiplayer scenarios

---

## 📦 Completed Archive

### Sprint 4: System Completeness (Dec 2024)

- [x] Server replication - Component sync system with 20Hz broadcast
- [x] Inventory stacking - Smart stacking with (item_type, count) tuples
- [x] Noise-based terrain generation - Perlin noise for all biomes
- [x] Player name labels - 3D billboarded TextNode tags
- [x] Horizontal acceleration and deceleration
- [x] Slope handling and surface normal projection
- [x] Liquid detection for water physics integration

### Ursina Migration (Dec 2024)

**Status**: Migration 100% complete. Zero active Ursina imports in project code.

- [x] Engine layer fully migrated to Panda3D
- [x] All engine tests use Panda3D vectors
- [x] Unified input system
- [x] Animation system migrated
- [x] HUD system migrated
- [x] Remote player rendering migrated
- [x] Removed Ursina from requirements.txt
- [x] Deprecated files removed

---

## 📊 Development Priorities

Based on recent work and project direction, focus areas are:

1. **Combat System Planning** - New feature area, requires design and planning
2. **Camera System Polish** - Fix zoom bug, consider ground-height constraints refinement
3. **Test Coverage** - Fix coordinate system issues in physics tests
4. **State Management** - Complete remaining architecture improvements
5. **Performance** - Profile and optimize for larger scale

**Next Steps:**

- Move forward with combat system design (per recent planning conversation)
- Address high-priority camera and test issues
- Continue ECS architecture refinements as needed for new features
