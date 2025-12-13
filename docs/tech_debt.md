# Tech Debt

## World Generation

- [x] ~~World generation is currently a placeholder~~ - Now uses proper sine-wave based height function with greedy meshing
- [ ] World generation uses simple sine waves - should be enhanced with proper noise (Perlin/Simplex) for more varied terrain
- [x] ~~Only generates 3x3 chunk grid - needs dynamic chunk loading/unloading for larger worlds~~ - Implemented with configurable radius and throttling
- [ ] UV coordinates are basic (0,0 to 1,1 per quad) - textures stretch across merged quads from greedy meshing
- [ ] Texture atlas system needed for varied block types (grass, stone, dirt, etc.)
- [ ] No biome system - all terrain uses same height function

## Physics System

- [x] ~~Basic raycast ground detection~~ - Implemented with configurable parameters
- [x] ~~Coyote time and jump buffering~~ - Implemented (0.2s windows)
- [x] ~~Variable jump height~~ - Implemented (early release = 55% velocity)
- [ ] Add horizontal acceleration and deceleration for smoother movement
- [ ] Implement air control (limited horizontal movement while airborne)
- [ ] Add slope handling and surface normal projection for angled terrain
- [x] ~~Wall collision detection~~ - Basic raycast wall check implemented in `physics.py`
- [ ] Improve wall sliding to allow smooth movement along walls
- [ ] Consider different ground checks for liquids, ladders, etc.
- [ ] Add sliding on steep slopes

## Performance

- [x] ~~Greedy meshing for terrain~~ - Implemented for top faces, reduces vertex count significantly
- [ ] Profile raycast ground detection performance with many entities (NPCs, projectiles)
- [ ] Consider spatial partitioning for large numbers of physics objects
- [ ] Side face meshing is non-greedy - could be optimized further
- [ ] No LOD system for distant chunks
- [x] ~~No frustum culling - all chunks always rendered~~ - Implemented basic frustum culling and view distance control

## Networking

- [x] ~~Basic TCP client/server~~ - Implemented with asyncio
- [x] ~~Position synchronization~~ - Players send updates at 10Hz
- [x] ~~Remote player rendering~~ - Simple cube representation
- [x] ~~Admin console system~~ - Basic slash commands implemented
- [ ] Add player interpolation/extrapolation for smoother remote movement (currently snaps to positions)
- [ ] Implement player names/labels above heads
- [ ] Add chat system for player communication (currently only admin console)
- [ ] Improve remote player visuals - use same body model as local player
- [ ] Consider UDP for position updates (TCP for important events) - currently all TCP
- [ ] Add connection timeout and retry logic
- [ ] Implement player customization (colors, names, skins)
- [ ] Add bandwidth optimization (delta compression, interest management)

## Camera System

- [x] ~~Third-person over-the-shoulder camera~~ - Implemented with offset and look-ahead
- [x] ~~Camera collision detection~~ - Raycasts to prevent clipping through terrain
- [ ] Camera smoothing/damping for less jerky movement
- [ ] Camera bob/sway for more organic feel when walking/running
- [ ] Adjustable camera distance (zoom in/out)
- [ ] Camera occlusion handling when blocked by objects (fade out or move closer)

## Visual Polish

- [ ] Player model is basic stacked cubes - needs proper character model
- [ ] Remote players render as single cubes - should match local player appearance
- [ ] No animations (walking, jumping, landing, idle)
- [ ] No particle effects (dust clouds, jump/land impacts)
- [ ] Basic static lighting - needs dynamic lighting and shadows
- [ ] Single texture for all terrain - texture atlas system needed
- [ ] No skybox or atmosphere rendering

## Input Handling

- [x] ~~Basic WASD movement~~ - Implemented
- [x] ~~Mouse look~~ - Implemented with camera pivot
- [x] ~~Space to jump~~ - Implemented with buffering
- [ ] No key rebinding / customization
- [ ] No gamepad/controller support
- [ ] Mouse sensitivity not configurable
- [ ] No mouse smoothing options

## Testing & Quality

- [x] ~~Basic physics tests~~ - Present in `tests/` directory
- [x] ~~Server admin tests~~ - Present in `tests/` directory
- [ ] No automated integration tests for multiplayer scenarios
- [ ] No performance benchmarks or regression tests
- [ ] No CI/CD pipeline
- [ ] Limited error handling in network code
- [ ] No client-side prediction or lag compensation testing
