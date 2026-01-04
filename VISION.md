# MyCraft Vision

## What is MyCraft?

MyCraft is a **beginner-friendly voxel game engine** designed for creating **action-RPG experiences** with **multiplayer at its core**. Whether you're building a world with friends in the visual map editor or adventuring together in-game, MyCraft makes game development accessible through *visual, tactile experiences* rather than code-first workflows.

### We Are

- **Built for absolute beginners** who want to create games without deep programming knowledge
- **Visual and tactile** with immediate feedback for every change you make
- **Multiplayer-native** in both the map editor (collaborate on worlds) and gameplay (adventure together)
- **Customization-focused** with tools for skinning, modeling, rigging, and texturing
- **Action-RPG oriented** for combat-focused, explorable voxel worlds
- **Powered by a solid foundation** (ECS architecture, Panda3D) abstracted for ease of use

### We Are Not

- A Minecraft clone or sandbox mining simulator
- Targeting MMO-scale networking (focused on LAN/small servers)
- Requiring programming expertise to create fun games
- A general-purpose voxel renderer (optimized for gameplay)

---

## Core Pillars

### 1. Beginner-First Design

**Accessible game development for absolute beginners.**

MyCraft prioritizes *doing* over *reading documentation*:

- **Visual workflows**: See your changes immediately
- **Tactile feedback**: Click, drag, paint, sculpt - not type
- **Learn by exploring**: Discover features naturally
- **Gradual depth**: Start simple, unlock complexity as you grow

**The engine's complexity is hidden**, allowing beginners to focus on creativity:

- ECS architecture powers the engine internally
- Game developers interact with simple, visual tools
- Advanced users can dive deeper when ready

### 2. Visual Map Editor

**Multiplayer collaborative world building.**

The map editor is a core feature, not an afterthought:

**Points of Interest (POI) Design:**

- Define locations with chunk-sized regions
- Configure biome generation parameters
- Set spawn points, encounter zones, landmarks
- Export directly to world generation

**Collaborative Editing:**

- Multiple creators work on the same map in real-time
- See each other's changes instantly
- Share and remix POI templates
- Built on the same multiplayer foundation as gameplay

**Visual, Tactile Interaction:**

- Paint terrain and biomes
- Place and configure entities with drag-and-drop
- Preview gameplay without leaving the editor
- Undo/redo with full history

### 3. Customization & Personalization

**Make it yours: skins, models, textures, and more.**

Customization is central to the MyCraft experience:

**Character Customization:**

- Skinning and recoloring
- Modeling with primitives (build from cubes, spheres, etc.)
- Extend existing models with custom parts
- Rigging for custom animations

**World Customization:**

- Block texturing and palette creation
- Biome theming and color schemes
- Environmental effects and atmosphere

**Sharing & Community:**

- Export and share custom assets
- Browse community creations
- Remix and build on others' work

### 4. Dual Multiplayer Experience

**Play together and create together.**

Both multiplayer modes are equally important:

**In-Game Multiplayer:**

- LAN-based adventuring with friends
- Real-time position sync at 20Hz
- Cooperative exploration and combat
- Zero-config discovery on local networks

**Editor Multiplayer:**

- Collaborative map building
- Real-time sync of world changes
- Shared creative sessions
- Built for remote and local collaboration

---

## Architecture Philosophy

### Abstracted Complexity

**Powerful engine, simple interface.**

MyCraft uses a robust technical foundation that stays out of the way:

| Layer | For Beginners | For Advanced Users |
|-------|---------------|-------------------|
| **Visual Tools** | Primary interface | Optional shortcuts |
| **Game Logic** | Pre-built templates | Scriptable systems |
| **Engine Core** | Invisible | Fully accessible |
| **ECS Architecture** | Abstracted | Direct access |

**Why ECS under the hood?**

- Enables complex game logic without spaghetti code
- Powers multiplayer sync efficiently
- Allows advanced users to extend without limits
- Maintains performance as games grow

### Proving Ground Model

**Test in games, extract to engine.**

Development flows through `voxel_world`:

1. **Prototype** features in the flagship game
2. **Validate** through playtesting with real users
3. **Extract** proven patterns to the engine
4. **Simplify** into beginner-friendly tools

---

## Target Audience

### Primary: Absolute Beginners

**First-time game creators and hobbyists.**

You should use MyCraft if you:

- Dream of making your own action-RPG world
- Prefer visual tools over writing code
- Want to create with friends in real-time
- Love customizing characters and worlds
- Learn best by doing, not reading

**No programming required** to create complete games.

### Secondary: Advanced Developers

**Power users who want to go deeper.**

MyCraft also supports experienced developers:

- Full access to ECS architecture
- Custom system development
- Engine extension and contribution
- Performance optimization

---

## Current Status

### Pre-Alpha Development (Milestone 1)

MyCraft is actively building the foundation:

- **Engine Core**: ECS, Physics, Networking ✅
- **voxel_world**: Proving ground game 🚧
- **Documentation**: Getting started guides 🚧
- **Visual Editor**: Planned for Milestone 3+

See [ROADMAP.md](ROADMAP.md) for milestones.

---

## Long-Term Vision

### Near-Term

- Complete engine foundation
- Release voxel_world alpha
- Establish beginner documentation

### Mid-Term

- **Visual Map Editor** with multiplayer collaboration
- **Customization Tools** for characters and worlds
- Community asset sharing

### Long-Term

- In-browser editor access
- Mobile companion apps
- Thriving creator community

---

## Get Involved

MyCraft welcomes contributors at all levels:

- **Playtesters**: Try voxel_world and give feedback
- **Documenters**: Help make guides beginner-friendly
- **Developers**: Extend the engine and tools
- **Creators**: Share custom content and ideas

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Document Info

*Last Updated: 2026-01-03*  
*Version: 2.1 - Color Combat Loop Integration*
