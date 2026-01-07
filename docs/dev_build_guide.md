# Color Combat Loop - Dev Build Guide

**Sprint**: v1.0-Hybrid Alpha | **Date**: 2026-01-05

This guide targets **remaining gaps** in the COLOR_COMBAT_LOOP core systems. Items are prioritized by loop-critical impact.

---

## 🔴 Critical: POI System Not Active

### 1. POI Spawning Integration

**Files**: [world_gen.py](file:///home/jamest/Desktop/dev/mycraft/games/voxel_world/systems/world_gen.py#L197-L252)  
**Effort**: ~4-6h  
**Status**: ⚠️ **BLOCKS ENTIRE COMBAT LOOP**

**Problem**: POI generation code exists but isn't integrated into chunk generation pipeline. No camps/shrines spawn → no enemies → no combat → no loot.

**Current State**:

- `CampGenerator` and `ShrineGenerator` implemented
- `_add_pois_to_chunk()` written but may not be called
- Entity spawn list returned but not processed

**Fix**:

1. Verify `_add_pois_to_chunk()` is called in chunk generation flow
2. Wire returned entities to `EntityFactory.create_enemy()`
3. Test camp spawning with debug visualization
4. Verify enemy AI activates on spawn

> **Note**: Until this is fixed, combat/enemy systems are **unverified and untestable**.

---

### 2. Loot Chest Interaction

**Files**: [interaction.py](file:///home/jamest/Desktop/dev/mycraft/engine/systems/interaction.py), [loot_system.py](file:///home/jamest/Desktop/dev/mycraft/games/voxel_world/systems/loot_system.py)  
**Effort**: ~2-3h

**Problem**: Camp/shrine chests are placed as blocks but have no interaction handler.

**Fix**:

1. Add `ChestComponent` to track contents
2. Wire `InteractionSystem` to handle "chest" block type
3. Spawn loot as pickup entities on open

---

## 🟡 High Priority: Loop Completion

### 3. Trading System

**Files**: NEW `trading_system.py`  
**Effort**: ~4-6h

**Design** (from COLOR_COMBAT_LOOP.md):

- Look at player + G = offer selected color
- Target sees prompt with Y/N
- Accept → color added to unlocked_colors
- Max distance: 5 units, 30s timeout

**Components needed**:

- `TradeOffer(offerer_id, target_id, color_name, timestamp)`
- Input binding for G, Y, N
- UI prompt (reuse existing HUD system)

---

### 4. Shrine Challenges + Preset Rewards

**Files**: NEW `shrine_challenge.py`, [poi_system.py](file:///home/jamest/Desktop/dev/mycraft/games/voxel_world/systems/poi_system.py)  
**Effort**: ~6-8h

**Design**:

- Shrines have interaction trigger area
- Entering triggers challenge (combat wave, parkour, puzzle)
- Completion unlocks preset (Knight, Ranger, Mage)

**Components needed**:

- `ShrineState(shrine_id, completed, preset_id)`
- `AvatarPresets` data definition
- Trigger zone detection (reuse pickup radius logic)

---

## 🟢 Medium Priority: Polish Items

### 5. Network Sync for Colors

**Files**: [network.py](file:///home/jamest/Desktop/dev/mycraft/engine/systems/network.py), [avatar_color_system.py](file:///home/jamest/Desktop/dev/mycraft/engine/systems/avatar_color_system.py)  
**Effort**: ~3-4h

**Problem**: `AvatarColors` changes don't replicate to other players.

**Fix**:

- Add `AvatarColors` to `SyncSystem` component list
- Serialize `body_color`, `bone_colors`, `temporary_color`, `temp_timer`
- Apply incoming color state to remote `EnemyVisual` / player avatars

---

### 6. Enemy HP Bars / Target Indicator

**Files**: [target_indicator.py](file:///home/jamest/Desktop/dev/mycraft/engine/rendering/target_indicator.py), [hud.py](file:///home/jamest/Desktop/dev/mycraft/engine/ui/hud.py)  
**Effort**: ~2-3h

**Problem**: Can't see enemy health during combat.

**Fix**:

- Add floating HP bar above enemies (billboard TextNode)
- Show on aggro, hide after de-aggro + delay
- Display tint color swatch next to name

---

### 7. Per-Bone Color UI

**Files**: NEW `color_customization_ui.py`  
**Effort**: ~4-6h

**Problem**: `AvatarColors.bone_colors` exists but no way to set it in-game.

**Fix**:

- Add customization panel (pause menu or dedicated UI)
- List unlocked colors as clickable swatches
- Bone selector (click avatar or list)
- Preview before apply

---

## 📊 Summary Table

| # | Item | Priority | Effort | Blocks |
|---|------|----------|--------|--------|
| 1 | Enemy Spawning | Critical | 2-3h | Combat flow |
| 2 | Chest Interaction | Critical | 2-3h | Loot flow |
| 3 | Trading System | High | 4-6h | Social loop |
| 4 | Shrine Challenges | High | 6-8h | Preset rewards |
| 5 | Network Color Sync | Medium | 3-4h | Multiplayer |
| 6 | Enemy HP Bars | Medium | 2-3h | Combat UX |
| 7 | Per-Bone UI | Medium | 4-6h | Customization depth |

**Total remaining**: ~23-34h estimated

---

## ✅ Systems Implemented (Unverified)

**Combat & Enemies** (code complete, untested due to POI blocker):

- Combat system (momentum damage, hit windows)
- Enemy AI (skeleton/zombie state machine)
- Loot drops (death → swatch → pickup)
- Enemy tinting (color seeding in camps)

**Color System** (functional):

- Color pickup / unlock_color()
- Color projectiles (throw, paint, 60s timer)
- Avatar color rendering (body_color, temp_color)
- Camp color seeding (deterministic per-world)

**World Generation** (functional):

- Shrine structure generation (5 biome variants)
- Camp structure generation
- POI placement logic (not integrated)

**Animation & Traversal** (basic implementation):

- Walk, sprint, jump (functional)
- Basic procedural animations
- Climbing, vaulting, advanced movement (planned, not implemented)
