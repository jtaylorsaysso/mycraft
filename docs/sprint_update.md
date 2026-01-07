# Sprint Update: Color Combat Loop

**Week of**: January 5, 2026  
**Milestone**: v1.0-Hybrid Alpha  
**Status**: 🔴 Critical Blocker - POI Integration Required

---

## Context: Where We Are

The COLOR_COMBAT_LOOP is the core gameplay pillar for v1.0-Hybrid Alpha. The design is:

**Intended Loop**: Explore → Find Camp → Fight Enemies → Collect Color Swatches → Customize Avatar → Share/Trade

**Current Reality**: Most systems are **code-complete but untestable** due to POI spawning not being integrated.

### What's Been Built

**Combat Systems** (implemented, unverified):

- Momentum-based damage (velocity scales damage)
- Enemy AI state machines (skeleton/zombie)
- Hit detection, health, death events
- Loot drop system (death → color swatch spawn)

**Color Systems** (functional):

- 8 starter colors + 12 loot colors
- Color projectiles (throw at friends, 60s paint effect)
- Avatar color customization (body color)
- Color pickup/unlock system

**World Systems** (partial):

- Camp/shrine structure generation (complete)
- Deterministic color seeding per camp (complete)
- POI spawning integration (**missing - critical blocker**)

**Animation & Movement** (basic):

- Walk, sprint, jump (functional)
- Climbing, vaulting (planned, not implemented)
- Combat animations (procedural, needs polish)

---

## Critical Blocker

### POI Spawning Not Integrated

**Issue**: POI generation code exists but isn't wired into chunk generation pipeline.  
**Impact**: **Entire combat loop is untestable**. No camps → no enemies → no combat → no loot.  
**Root Cause**: `_add_pois_to_chunk()` may not be called during world generation, or entities aren't spawned from returned data.  
**Estimated Fix**: 4-6 hours to integrate and verify

---

## What's Implemented (Unverified) ⚠️

### Combat Flow

| Feature | Status | Notes |
|---------|--------|-------|
| Momentum combat | 🟡 Unverified | Code complete, no enemies to test |
| Skeleton AI | 🟡 Unverified | State machine implemented |
| Zombie AI | 🟡 Unverified | Slower, tankier variant |
| Enemy tinting | 🟡 Unverified | Color seeding in camp generator |
| Hit detection | 🟡 Unverified | Sphere-based collision |

### Color System

| Feature | Status | Notes |
|---------|--------|-------|
| Starter palette (8) | ✅ Complete | Available at game start |
| Loot palette (12) | ✅ Complete | Crimson, Gold, Forest, etc. |
| Color drops | 🟡 Unverified | Code exists, no enemies to test |
| Pickup collection | 🟡 Unverified | System implemented |
| Body color | ✅ Complete | `C` key cycles colors |
| Temp color override | ✅ Complete | 60s duration, visual sync |

### Animation & Traversal

| Feature | Status | Notes |
|---------|--------|-------|
| Walk | ✅ Complete | Basic locomotion |
| Sprint | ✅ Complete | Speed boost |
| Jump | ✅ Complete | Single jump |
| Climbing | ❌ Planned | Not implemented |
| Vaulting | ❌ Planned | Not implemented |
| Advanced movement | ❌ Planned | Wall-run, glide, etc. |
| Combat animations | 🟡 Basic | Procedural, needs polish |

### Projectile System

| Feature | Status | Notes |
|---------|--------|-------|
| Throw color | ✅ Complete | `T` key, aim with camera |
| Hit detection | ✅ Complete | Sphere collision |
| Paint effect | ✅ Complete | Target turns your color |
| Particle splat | ✅ Complete | VFX on impact |

---

## What's Not Working ⚠️

### POI System Not Integrated (CRITICAL)

**Issue**: POIs (camps/shrines) are not spawning in the world at all.  
**Impact**: **Entire combat loop is untestable**. No camps → no enemies → no combat → no loot.  
**Root Cause**: POI generation code exists but isn't wired into chunk generation pipeline.  
**ETA**: 4-6 hours to integrate and verify

### Trading System

**Issue**: Not implemented yet.  
**Impact**: Can't share colors with teammates.  
**ETA**: 4-6 hours to build

### Shrine Challenges

**Issue**: Shrines are decorative only, no gameplay.  
**Impact**: No preset unlocks (Knight, Ranger, Mage).  
**ETA**: 6-8 hours to build

### Per-Bone Customization UI

**Issue**: Data support exists, no UI to access it.  
**Impact**: Can't customize individual limbs.  
**ETA**: 4-6 hours to build

---

## Open Design Questions

These questions need design team input to guide implementation priorities and scope:

### 1. POI Spawning & Density ⚡ (Unblocks Everything)

**Context**: Once POI integration is fixed, we need to tune spawn rates.

- What's the ideal camp/shrine density? Current code: ~30% spawn chance per chunk.
- Should camps be more common than shrines, or equal distribution?
- How far should players travel to find their first combat encounter?

**Recommendation**: Start conservative (lower density), tune up based on playtest feedback.

---

### 2. Shrine Challenge Scope 🎯 (Defines Implementation Effort)

**Context**: 3 shrine types planned (combat, parkour, puzzle). None implemented yet.

- Should v1.0-Hybrid include **all three** types or focus on **combat only**?
- What's the minimum viable challenge? ("Defeat 3 waves" vs complex mechanics)
- Are preset rewards (Knight, Ranger, Mage) valuable enough to motivate completion?

**Recommendation**: Combat shrines only for v1.0, defer parkour/puzzle to v1.1.

---

### 3. Trading System Priority 🤝 (Affects Sprint Timeline)

**Context**: Trading is designed but not implemented. Estimated 4-6h to build.

- Is trading essential for v1.0-Hybrid playtest, or can it wait?
- Should recipients preview the color before accepting? (adds UI complexity)
- Should there be a trade history/log for multiplayer coordination?

**Recommendation**: Defer to post-playtest if time is tight. Color projectiles provide social interaction.

---

### 4. Animation Polish Threshold 🎨 (Defines "Done")

**Context**: Animations are basic/procedural. Combat "works" but may not "feel good."

- How much animation polish is needed before playtest?
- Should we prioritize combat hit reactions, or is basic procedural acceptable?
- Are climbing/vaulting required for v1.0-Hybrid, or defer to v1.1?

**Recommendation**: Basic is acceptable for alpha. Focus on combat feel over animation fidelity.

---

### 5. Death & Color Loss ⚰️ (Design Philosophy)

**Context**: Design doc mentions dropping color swatches on death, but unclear if v1.0 scope.

- Should players drop **unlocked colors** on death, or just **equipped items**?
- Should swatches be recoverable (Elden Ring style) or lost permanently?
- Does death need to be punishing at all in a casual-first game?

**Recommendation**: Defer color loss to v1.1. Keep death low-stakes for alpha playtest.

---

### 6. Color Acquisition Pacing 🎨 (Player Progression)

**Context**: Players start with 8 colors, can unlock 12 more from loot.

- Should rare colors (crimson, gold, navy) be harder to find than common ones?
- How many colors should a player unlock in their first hour?
- Should camp color palettes be 2-4 colors (current) or narrower/wider?

**Recommendation**: Keep current 2-4 random colors per camp. Tune rarity post-playtest.

---

### 7. Per-Bone Customization UI 🖌️ (Feature Scope)

**Context**: Data structure exists, no UI to access it.

- Is per-bone customization essential for v1.0, or is body color sufficient?
- Should the UI be in-game (pause menu) or separate customization screen?
- How complex should the UI be? (simple list vs visual bone picker)

**Recommendation**: Defer to v1.1. Body color + projectiles are enough for social loop validation.

---

### 8. Combat Difficulty Tuning ⚔️ (Needs Playtesting)

**Context**: No enemies to test against yet, but systems are implemented.

- What should skeleton vs zombie health/damage feel like in practice?
- Should momentum damage be linear (`base + velocity`) or exponential?
- Is the 2.0 unit hit range too generous or too restrictive?

**Recommendation**: Keep current values, gather playtest data, iterate in v1.0.1 patch.

---

### 9. Multiplayer Color Sync 🌐 (Technical Priority)

**Context**: Color changes may not replicate to other players yet.

- Is seeing other players' customization critical for the social loop?
- Should temporary overrides (from projectiles) sync immediately or with delay?
- What happens if network sync fails? (fallback to default colors?)

**Recommendation**: Sync is important for social validation. Prioritize after POI integration.

---

### 10. Playtest Success Metrics 📊 (Defines Goals)

**Context**: Design doc has success criteria, but some are blocked by POI issue.

- Which metrics are **must-measure** vs nice-to-have for first playtest?
- Focus on "color projectiles create laughter" or "combat feels skill-based"?
- What's the minimum viable loop to validate the core concept?

**Recommendation**: Prioritize social metrics (laughter, color throwing) over combat depth for alpha.

---

## What Playtesters Will Experience

### ✅ Currently Playable

- Spawning in a generated world (basic biomes)
- Walking, sprinting, jumping
- Changing avatar color with `C` (cycles starter colors)
- Throwing colors at each other with `T`
- Being "painted" for 60 seconds

### ⚠️ Implemented But Broken

- **POIs don't spawn** (camps/shrines missing from world)
- **No enemies** (can't test combat)
- **No loot** (no source for color swatches)
- Chests exist in POI code but never placed

### ❌ Not Available

- Combat (blocked by POI spawning)
- Enemy encounters
- Color swatch collection
- Trading colors
- Preset unlocks
- Shrine challenges
- Per-bone customization UI
- Advanced movement (climbing, vaulting)

---

## Metrics to Watch

From the design doc success criteria:

- [ ] Players identify enemy loot by tint *(blocked - no POIs)*
- [ ] 80%+ customize avatar in first session *(partially testable - only starter colors)*
- [ ] Color projectiles used at least once per 10-min *(testable now)*
- [ ] Trading occurs naturally *(blocked - not implemented)*
- [ ] Playtesters laugh when painted *(testable now)*
- [ ] "One more color" keeps players engaged *(blocked - no loot source)*

---

## Next Sprint Focus

1. **Integrate POI spawning** (CRITICAL - unblocks entire combat loop)
2. **Verify enemy AI in-game** (test combat systems)
3. **Test loot drop → pickup flow** (validate color collection)
4. **Polish animations** (combat feels basic)
5. **Build trading system** (if POI integration completes early)

---

*Prepared by: Engineering Team*  
*Next update: January 12, 2026*
