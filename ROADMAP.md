# MyCraft Roadmap

**Last Updated**: 2025-12-31  
**Current Version**: v0.2 - Combat Prototype

> [!IMPORTANT]
> **Semantic Versioning Adopted**: This roadmap now uses semantic versioning (v0.x → v1.0 → v2.0 → v3.0) aligned with the design team's vision.

---

## Overview

This roadmap outlines the high-level milestones for MyCraft's development, aligned with the design vision of creating **"a beautiful, open sandbox where players explore, build, collect, decorate, and play their own way."**

Sprint-level details and task tracking are managed in [`docs/tech_debt.md`](docs/tech_debt.md).

---

## Version History & Semantic Versioning

### Versioning Scheme

- **v0.x - Pre-Alpha**: Engine foundation and prototyping
- **v1.0 - Alpha**: Core gameplay loop functional ("Can I play for 1 hour?")
- **v2.0 - Beta**: Major pillars implemented ("Can I play for 10+ hours?")
- **v3.0 - Release**: Full vision realized ("I live there, not just beat it")

### Patch & Minor Updates

- **Minor versions** (v1.1, v1.2): New features, content additions, backward compatible
- **Patch versions** (v1.0.1): Bug fixes, performance improvements

---

## v0.x - Pre-Alpha: Engine Foundation

### v0.1 - Engine Foundation ✅

**Status**: Mostly Complete (Milestone 1)  
**Goal**: Establish core engine systems and architecture

#### Completed ✅

- **ECS Architecture**: World, Entity, Component, System pattern
- **Physics System**: Kinematic character controller with slope handling
- **Networking**: TCP client/server with LAN discovery
- **Rendering**: Panda3D integration, mesh building, texture atlas
- **Water Physics**: Buoyancy and swimming mechanics
- **Animation**: Layered animation system (procedural + keyframe)
- **Testing**: Unit and integration test framework (257/294 tests passing)

#### Remaining Work 🚧

- Fix remaining test failures (37 tests, mostly minor edge cases)
- Complete documentation pass (API references, developer guides)
- Performance baseline established

---

### v0.2 - Combat Prototype 🚧

**Status**: In Progress (Milestone 2, Current Sprint)  
**Goal**: Timing-based combat with dodge/parry mechanics

#### Completed ✅

- Layered animation system with combat clips (attacks, dodge, parry)
- Combat state management (CombatState, Stamina components)
- Attack/Dodge/Parry mechanics with timing windows
- Root motion for attack lunges
- Animation events for hit detection
- Camera polish (collision, bob, zoom, mode-based architecture)
- Stamina drain and regeneration

#### In Progress 🚧

- Combat animation integration (Phase 2: Dodge, Phase 3: Parry)
- Enemy AI framework (Skeleton enemy planned)
- Combat testing and tuning

---

## v1.0 - Alpha: Core Gameplay Loop

> **Theme**: "Can I play the game and have fun for 1 hour?"

**Status**: Planned (Milestone 2 completion)  
**Target**: ~6-8 weeks (Est. Feb 2026)  
**Goal**: Deliver playable alpha with exploration → challenge → reward loop

### Features

#### Core Systems ✅

- Timing-based combat (dodge/parry)
- Movement mechanics (walk, run, jump, climb, vault)
- Multiplayer co-op (networking infrastructure ready)
- 8 normal biomes (Plains, Forest, Rocky, Desert, Mountain, Canyon, River, Beach/Swamp)

#### New for v1.0 🎯

- **POI System**: Discoverable Points of Interest
  - Challenge Shrines (3-5 types)
  - Visible landmarks from far away
  - Reward chests with basic loot
- **First Enemy Type**: Skeleton
  - Telegraphed attacks (1.5s windup)
  - AI state machine (Idle → Aggro → Windup → Attack → Recovery)
  - Health: 50, Damage: 20
- **Death System**:
  - Respawn at last safe point
  - Item recovery (Elden Ring-style, no time limit)
  - Death = inconvenience, not punishment
- **Balanced Difficulty**:
  - Casual-first approach (default)
  - Accessible to broad audience
  - Optional difficulty variants deprioritized for now
- **Basic Loot**:
  - Loot drops from enemies
  - Collectible items in shrines
  - Inventory system functional

### Success Criteria

- [ ] Player can explore → find POI → defeat enemies → collect loot
- [ ] Combat feels fun and skill-based
- [ ] Multiplayer supports 2-4 players co-op
- [ ] Death/respawn loop is forgiving
- [ ] 1-hour playtest reveals engaging core loop

### Effort Estimate

- POI System: ~2-3 weeks
- Skeleton Enemy AI: ~1-2 weeks
- Death System: ~1 week
- Basic Loot: ~1 week
- **Total**: ~6-8 weeks

---

## v1.1 - v1.3: Content Expansion

> **Theme**: "Add variety to the 1-hour loop"

**Status**: Planned (Milestone 2.5)  
**Target**: ~2-3 months (Est. Apr-May 2026)  
**Goal**: Expand content without adding new systems

### v1.1 - Enemy Variety 🎯

**Priority**: High  
**Effort**: ~2-3 weeks

- **Zombie Enemy** (requested by design team)
  - Must look like zombies (design requirement)
  - Shambling movement, slower but higher health
  - Group behavior (zombies hunt in packs)
- **2-3 Additional Enemy Types**:
  - Archer (ranged combat)
  - Brute (high damage, slow attacks)
  - Agile (fast, low health)
  
### v1.2 - More POI Types 🎯

**Priority**: Medium  
**Effort**: ~2-3 weeks

- **Caves**: Underground exploration
- **Camps**: Enemy outposts with loot
- **Towers**: Vertical climbing challenges
- **Ruins**: Puzzle-based POIs

### v1.3 - Fantasy Biomes 🎯

**Priority**: Medium  
**Effort**: ~2-3 weeks

- **Magical Forests**: Glowing trees, colorful atmosphere
- **Crystal Caves**: Geometric crystals, light refraction
- **Enchanted Plains**: Floating islands, sky platforms
- **Fantasy = magical and colorful, not scary** (design requirement)

### Success Criteria

- [ ] Enemy combat feels varied and engaging
- [ ] POIs have distinct identities (cave ≠ shrine)
- [ ] Fantasy biomes feel whimsical and inviting
- [ ] Players want to explore for variety, not just rewards

---

## v2.0 - Beta: Building & Progression

> [!IMPORTANT]
> **MAJOR MILESTONE**: Implements the **Building & Hoarding pillar** (critical design requirement)

> **Theme**: "Can I play for 10+ hours and feel ownership?"

**Status**: Planned (Milestone 5)  
**Target**: ~4-6 months (Est. Jun-Aug 2026)  
**Goal**: Deliver the building/hoarding pillar and progression systems

### Features

#### Building & Crafting 🏗️

**Priority**: Critical (Major design pillar)  
**Effort**: ~4-6 weeks

- **Chunk-Based Build Zones**: Tied to POIs (16x16 chunk building areas)
- **Modular Building**: Fallout-style but improved
  - Place walls, floors, roofs
  - Snap-to-grid system
  - Free-form voxel placement option
- **Prefab System**: Pre-built structures (houses, towers, bridges)
- **Item Interactions**:
  - Pick up any placed item
  - Break down for parts
  - Upgrade (wood → stone → metal)
  - Use as decoration
- **Save/Load Builds**: Export/reload builds, future seed into world generation

#### Skill Progression 📈

**Priority**: High  
**Effort**: ~2-3 weeks

- **Simple Skill Tree** (Fallout 4 / Spider-Man style)
  - Small, not sprawling (design requirement)
  - Skills unlock options, not raw power
- **4 Skill Categories**:
  - **Combat**: Combo chains, weapon variety, stun attacks
  - **Traversal**: Wall-run, gliding, double-jump
  - **Loot/Crafting**: Auto-pickup, better salvage, rare finds
  - **Building**: Larger zones, faster construction, advanced materials

#### Loot & Economy 💰

**Priority**: High  
**Effort**: ~2-3 weeks

- **Unified Currency**: Fallout caps-style (not rare or grindy)
- **Collectibles**: Clothing, cosmetics, décor items
- **Hoarding Support**: Storage chests, display cases, trophy rooms

#### Visual Polish 🎨

**Priority**: Medium-High  
**Effort**: ~3-4 weeks

- **Dynamic Lighting**: Shadows, day/night transitions
- **Skybox & Atmosphere**: "Skyrim-like mood" (design requirement)
- **Weather System**: Rain, fog, wind effects
- **Particle Effects**: Dust clouds, magic sparkles, impact VFX

### Success Criteria

- [ ] Players can build, customize, and decorate bases
- [ ] Skill tree provides meaningful choices
- [ ] Loot feels rewarding and collectible
- [ ] World atmosphere is beautiful and inviting
- [ ] 10+ hour playtest shows sustained engagement

---

## v2.1 - v2.3: Polish & Depth

> **Theme**: "Make it beautiful and engaging long-term"

**Status**: Planned (Milestone 4 completion)  
**Target**: ~6-9 months (Est. Sep-Nov 2026)  
**Goal**: Polish, optional modes, and advanced features

### v2.1 - Visual Excellence 🎨

- **Advanced Lighting**: God rays, ambient occlusion
- **Improved Skyboxes**: Per-biome custom skies
- **Seasonal Weather**: Storms, snow, clear skies
- **Voxel Particle System**: Enhanced VFX library

> [!NOTE]
> **Difficulty Systems Deprioritized**: Adaptive difficulty and hardcore mode are not a strong focus currently. The game uses a casual-first approach with broad accessibility as the default stance. These features may be revisited in future versions based on player feedback.

### v2.2 - Advanced Building 🏗️

- **Prefab Palette**: 20+ pre-built structures
- **Build Blueprints**: Share .json files with friends
- **World Gen Integration**: Seed player builds into new worlds
- **Advanced Materials**: Glass, metal, decorative blocks

### v2.3 - Character Customization 🎨

- **Texture Customization**: Paint your avatar
- **Color Palettes**: Preset and custom colors
- **Primitive Modeling**: Add parts to avatar (hats, capes)
- **Asset Sharing**: Export/import skins

### Success Criteria

- [ ] Game looks and feels premium (Skyrim-like atmosphere achieved)
- [ ] Building system rivals Fallout 4 (but better)
- [ ] Character customization encourages self-expression
- [ ] Visual polish supports the "Skyrim-like mood" design goal

---

## v3.0 - Full Release: "Living World"

> **Theme**: "I live there, not just beat it"

**Status**: Long-Term Vision (Milestone 6+)  
**Target**: ~12+ months (Est. 2027+)  
**Goal**: Realize full design vision with community ecosystem

### Weirdness Content 🐉

- **Fantasy + Futuristic Tech Mashup** (design requirement)
  - Dragons with missile launchers 🚀🐉
  - Unicorns, strange mounts
  - RIFTS-style lore explanation
- **Epic Encounters**: Dragon boss fights, mechs in fantasy ruins

### Community Ecosystem 🌐

- **Visual Level Editor**: Multiplayer collaborative world building (Milestone 3)
- **Asset Marketplace**: Community-created content sharing
- **Build Gallery**: Showcase player creations
- **Mod Support**: Lua/Python scripting

### Advanced Systems ⚙️

- **Advanced AI**: Pathfinding, behavior trees, NPC dialogue
- **3D Spatial Audio**: Directional sound, dynamic music
- **Optimization**: LOD system, GPU acceleration, proper frustum culling

---

## Release Philosophy

### Versioning

- **Major versions** (v1.0, v2.0, v3.0): Aligned with design milestones (Alpha, Beta, Release)
- **Minor versions** (v1.1, v1.2): New features, content additions, backward compatible
- **Patch versions** (v1.0.1): Bug fixes, performance improvements

### Release Cadence

- **Major releases**: When milestone success criteria fully met (no fixed timeline)
- **Minor releases**: Every 3-6 weeks during active development
- **Patch releases**: As needed for critical bugs

### Stability Guarantee

- Engine API stability prioritized after v1.0 Alpha
- Deprecation warnings for 2 minor versions before removal
- Migration guides for breaking changes
- Save file compatibility maintained within major versions

---

## Design Alignment

> [!NOTE]
> This roadmap addresses gaps identified in Design Alignment Analysis (2025-12-31)

### Critical Gaps Addressed

1. **Building & Hoarding Pillar** → v2.0 Beta (Milestone 5)
2. **Skill Progression System** → v2.0 Beta
3. **Loot & Currency Economy** → v2.0 Beta
4. **Visual Polish (Skyrim-like atmosphere)** → v2.0 + v2.1
5. **Fantasy Biomes** → v1.3 Content Expansion
6. **Advanced Building Features** → v2.2
7. **Character Customization** → v2.3
8. **Weirdness Content (dragons, tech)** → v3.0 Long-Term

**Note**: Adaptive difficulty and hardcore mode deprioritized per casual-first design approach.

### Philosophical Alignment Confirmed ✅

- Non-linear exploration ✅ (Implemented)
- Timing-based combat with optional parry ✅ (Implemented)
- Casual-friendly first, hardcore optional ✅ (Casual-first approach)
- Death = inconvenience, not punishment ✅ (v1.0 death system)
- No forced linear quests ✅ (By design)
- Multiplayer co-op ✅ (Implemented)

---

## Current Sprint

See [`docs/tech_debt.md`](docs/tech_debt.md) for:

- Active sprint goals (currently Sprint 6: Combat Prototype → v0.2)
- Detailed task breakdown
- Technical debt tracking
- Completed features and next steps

---

## Contributing to the Roadmap

Have ideas for MyCraft's future? We welcome:

- **Feature proposals**: Open an issue with the `enhancement` label
- **Milestone feedback**: Comment on roadmap discussions
- **Implementation PRs**: See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

---

*Last Updated: 2025-12-31*  
*Version: v0.2 (Combat Prototype)*  
*Extended with Semantic Versioning aligned to Design Vision*
