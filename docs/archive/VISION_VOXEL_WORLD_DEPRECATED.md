# Voxel World Vision

## What is Voxel World?

Voxel World is an **exploration-driven action adventure** with **momentum-based combat** set in a procedurally generated voxel landscape. Players traverse vast biomes, discover Points of Interest, and overcome challenges through skillful movement and timing-based combat—alone or with friends.

### Inspirations

- **Breath of the Wild**: Open-world exploration, emergent discovery, "what's over that hill?"
- **Shadow of the Colossus**: Epic encounters, climbing mechanics, deliberate combat pacing
- **Assassin's Creed**: Fluid traversal, parkour movement, satisfying momentum

### We Are

- **Exploration-first** with rewarding discovery around every corner
- **Movement-focused** with deep, satisfying traversal mechanics
- **Combat through momentum** where timing and positioning matter more than stats
- **Cooperative PvE** designed for adventuring with friends
- **Point of Interest driven** with hand-crafted challenges in a procedural world

### We Are Not

- A building/creative sandbox (that's the engine's domain)
- A survival game with hunger meters and crafting grind
- A stat-heavy RPG with skill trees and gear scores
- Competitive PvP

---

## Core Pillars

### 1. Deep Movement Mechanics

**Traversal is gameplay, not just travel.**

Movement should feel like a skill to master:

- **Momentum-based**: Running, sliding, vaulting, climbing
- **Expressive traversal**: Multiple ways to reach any destination
- **Risk/reward**: Faster routes require more skill
- **Environmental puzzle**: Terrain is an obstacle and a tool

**Movement Verbs:**
<!-- TODO: Tie these to Stamina costs (Sprint ~10/s, Climb ~15/s, Vault ~10 flat) -->

- Sprint, slide, vault, climb, grab
- Walljump, wall-run (future)
- Swim, dive, water traversal
- Glide/descend (future)

### 2. Timing-Based Combat

**Third-person action where skill matters.**

Combat emphasizes player mastery over character stats:

- **Timing windows**: Dodge, parry, counterattack
- **Positional combat**: Flanking, backstabs, high ground
- **Momentum integration**: Combat flows from movement
- **Readable enemies**: Clear tells, fair challenge

**Combat Goals:**

- Weighty, impactful hits
- Simple inputs, deep mastery curve
- Combat arenas integrated into terrain
- Boss encounters as climactic moments

### 3. Exploration & Discovery

**The world rewards curiosity.**

Every horizon hides something worth finding:

- **Visual landmarks**: "What's that structure over there?"
- **Emergent discovery**: Stumble upon secrets, not just markers
- **Varied biomes**: 9 distinct environments to explore
- **Vertical world**: Caves below, peaks above

### 4. Point of Interest Gameplay Loop

**The core loop: Explore → Discover → Challenge → Reward**

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Spawn  ──►  Explore  ──►  Spot PoI  ──►  Reach   │
│                                                     │
│     ▲                                       │       │
│     │                                       ▼       │
│     │                                               │
│   Explore  ◄──  Collect Reward  ◄──  Overcome      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Points of Interest:**

- **Challenge Shrines**: Movement/combat puzzles
- **Enemy Camps**: Combat encounters
- **Ruins/Dungeons**: Exploration + combat hybrid
- **Colossi**: Epic boss encounters (SotC-style)
- **Secrets**: Hidden treasures for observant explorers

### 5. Cooperative Adventure

**Better with friends.**

Designed from the ground up for coop:

- **Shared exploration**: Discover together
- **Complementary combat**: Coordinate attacks, distract enemies
- **No friendly fire**: Focus on the adventure, not griefing
- **Drop-in/drop-out**: Seamless multiplayer sessions

---

## Target Experience

### The First Hour

1. **Spawn** in a safe area with basic controls tutorial
2. **See** a mysterious structure on the horizon
3. **Journey** across varied terrain, learning movement
4. **Arrive** at first PoI—a small combat challenge
5. **Overcome** with timing and positioning
6. **Reward** hints at deeper mysteries
7. **Explore** with new confidence, spotting next destination

### The Ideal Session

- 30–60 minutes of meaningful progress
- At least one "wow" discovery moment
- One challenging encounter overcome
- Satisfying traversal sequences
- (Coop) Memorable moments with friends

---

## Current State

### Implemented ✅

- **World Generation**: 9 biomes with Perlin noise terrain
- **Movement**: Acceleration-based with slope physics
<!-- TODO: Integrate Stamina drain for sprints and climbs -->
- **Physics**: Jumping with coyote time, water swimming
- **Multiplayer**: LAN coop with real-time sync
- **Camera**: Third-person with first-person toggle

### Next Priorities 🚧

- **Enhanced traversal**: Climbing, vaulting, ledge mechanics
- **Combat foundation**: Attack, dodge, enemy AI
- **First PoI**: Simple challenge shrine prototype
- **Reward system**: Basic progression/unlocks

### Future Vision 📋

- **Full movement kit**: Wall mechanics, tool-assisted movement (grappling hooks, ropes)
- **Combat depth**: Parry, combos, boss encounters
- **PoI variety**: Multiple challenge types
- **Progression**: Unlockable abilities, upgrades

---

## Design Principles

### Movement First

Every feature should complement exploration:

- New abilities enhance traversal options
- Combat can be evaded through clever movement
- World design encourages creative pathing

### Readable Challenges

Players should understand:

- Where they need to go (landmarks, sight lines)
- What they need to do (clear objectives)
- Why they failed (fair difficulty)

### Cooperative by Design

Features work better together:

- Puzzles with optional coop shortcuts
- Combat that rewards coordination
- Exploration that's enhanced by multiple perspectives

### Demo Scope

For the functional demo:

- **One complete loop**: Spawn → PoI → Reward
- **Core movement feel**: Sprint, jump, climb basics
- **Combat proof**: One enemy type, basic combat
- **Coop working**: Two players exploring together

---

## Technical Foundation

Voxel World leverages the MyCraft engine:

| Feature | Engine System |
|---------|---------------|
| Terrain | `TerrainSystem` with biome generation |
| Movement | `PlayerControlSystem` with physics |
| Combat | (Planned) `CombatSystem` |
| Multiplayer | `SyncSystem` with LAN discovery |
| Camera | Third-person orbital controller |

---

## Get Involved

- **Playtest**: Experience exploration, report rough edges
- **Design feedback**: What feels good? What's missing?
- **Content ideas**: PoI concepts, enemy designs, biome themes

---

*Last Updated: 2025-12-23*  
*Version: 1.0 - Exploration & Combat Vision*
