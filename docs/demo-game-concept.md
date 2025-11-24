# MyCraft: Co-op Dungeon Crawler - Game Direction

## Core Vision

**Family co-op dungeon crawler in a voxel world.** 2-4 players on LAN, clearing hand-crafted dungeons together. Think Zelda dungeons meets Minecraft blocks meets family game night.

## What This Game IS

- **Room-based dungeon crawling** - Each 16x16 chunk is a designed encounter
- **Action combat** - Sword swings, enemy patterns, timing and positioning matter
- **Spatial puzzles** - Push blocks, hit switches, navigate rooms (Zelda DNA)
- **Co-op focused** - Designed for 2-4 players working together
- **Campaign structure** - 5-10 dungeons with progression, not infinite sandbox
- **LAN multiplayer** - Family plays together, no cloud/servers needed

## What This Game IS NOT

- **NOT** a building/crafting game (no block placement by players)
- **NOT** an MMO (no persistent servers, economy, hundreds of players)
- **NOT** procedurally generated (handcrafted dungeons, maybe proc overworld later)
- **NOT** a solo experience first (co-op is the design priority)
- **NOT** about mining or resource gathering

## The Core Loop

1. Enter dungeon room (chunk loads)
2. Fight enemies or solve puzzle (or both)
3. Door unlocks, progress to next room
4. Boss room at end
5. Get reward, unlock next dungeon

## Design Pillars

### 1. Readable Spatial Design

- Grid-based rooms (16x16 tiles)
- Clear sight lines for combat and puzzles
- No noisy terrain - broad shapes, gentle slopes
- Block-based obstacles are obvious and intentional

### 2. Fair Action Combat

- 3-hit kills (both player and basic enemies)
- Knockback gives breathing room
- Patterns you can learn and master
- Timing matters more than stats

### 3. Co-op Synergy

- Puzzles that benefit from coordination
- Enemy encounters scaled for player count
- Shared progression, individual skill expression
- Revive mechanics (future: help downed teammates)

### 4. Modular Content

- Rooms are self-contained (like D&D encounters)
- Mix and match rooms into dungeons
- Reusable enemy/puzzle types across dungeons
- Foundation for eventual dungeon editor

## Current Milestone: Room 1 Prototype

**Goal**: Prove the core loop is fun with cubes

**Must Have**:

- One 16x16 room with walls
- One enemy (green slime cube, 3 HP, patrol + aggro + chase)
- One puzzle (movable block + floor switch)
- Sword swing (red hitbox cube, 0.3 sec duration, knockback)
- Locked door that opens when puzzle solved

**Success Criteria**:

- Combat feels good (hitting slime is satisfying)
- Puzzle is solvable (block on switch = door opens)
- Player can choose to fight or avoid slime
- You smile when playing it

**Out of Scope for Room 1**:

- Networking (turn it off for now)
- Pretty graphics/textures (colored cubes only)
- Animation/rigging (position changes, no interpolation needed)
- Sound effects (later)
- UI/HUD (maybe just HP text)

## Next Steps After Room 1

**Phase 1**: First Complete Dungeon

- 3-5 connected rooms
- One mini-boss
- New enemy type with different pattern
- Victory condition

**Phase 2**: Re-enable Multiplayer

- Two players can clear dungeon together
- Test co-op puzzle solving
- Balance enemy count for 2 players

**Phase 3**: Second Dungeon

- New theme/aesthetic (different colored blocks)
- New mechanic (bombs? hookshot? something)
- More complex puzzles

## Technical Constraints (Your Advantages)

✅ **16x16x16 chunks** - Perfect room size, already built
✅ **Physics system** - Reusable for all entities, already built  
✅ **Ground-level terrain** - Simple collision, already built
✅ **Third-person camera** - Combat visibility, already built
✅ **Networking foundation** - Turn on when needed, already built

## Design Constraints (Keep You Focused)

🎯 **No block destruction** - Static geometry, predictable layouts
🎯 **Grid-locked movement** - Smooth but spatially clear
🎯 **2D-thinking in 3D** - Design on graph paper, build in voxels
🎯 **Paper first, code second** - Validate room design before implementing

## The Reminder for Future You

**When you get lost in the weeds again:**

Stop. Ask yourself:

1. "Can my family play this right now and have fun?"
2. If no: "What's the ONE thing blocking fun?"
3. Build only that thing
4. Go to step 1

**If you're working on something and can't answer "how does this make Room 1 more fun?" - you're in the weeds.**

Engine work is allowed, but only after you've proven the game loop works. Build game first, extract engine patterns second.

## The North Star

Your family sits down for game night. They connect to your LAN. They clear a dungeon together. They argue about strategy. Someone dies and laughs. They beat the boss and cheer. They ask "when's the next dungeon ready?"

That's the game. Everything else is noise.

---

**Current Task**: Build Room 1 with colored cubes. Get the slime hopping and the sword swinging. Make it fun in the ugliest possible way. Polish comes later.
