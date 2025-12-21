# MyCraft Roadmap

## Overview

This roadmap outlines the high-level milestones for MyCraft's development. Sprint-level details and task tracking are managed in [`docs/tech_debt.md`](docs/tech_debt.md).

---

## Milestone 1: Engine Foundation 🚧

**Status**: In Progress  
**Goal**: Establish core engine systems and architecture

### Completed ✅

- **ECS Architecture**: World, Entity, Component, System pattern
- **Physics System**: Kinematic character controller with slope handling
- **Networking**: TCP client/server with LAN discovery
- **Rendering**: Panda3D integration, mesh building, texture atlas
- **Water Physics**: Buoyancy and swimming mechanics
- **Animation**: Procedural character animations
- **Testing**: Unit and integration test framework

### In Progress 🚧

- **Documentation**: API references and developer guides
- **Onboarding Docs**: Getting Started Guide, Player Guide polish, troubleshooting FAQ
- **Test Infrastructure**: Fix 15 collection errors, establish CI baseline
- **Performance**: Optimization and benchmarking
- **Polish**: Bug fixes and UX improvements

### Milestone 1 Success Criteria

- [ ] Core engine systems documented with API references
- [ ] Test coverage >70% for engine modules (currently 76 tests, 15 with collection errors)
- [ ] All test collection errors resolved
- [ ] Performance baseline established and met
- [ ] voxel_world demonstrates all engine capabilities
- [ ] Getting Started Guide complete (text-only)
- [ ] Player Guide polished for playtester onboarding
- [ ] Launcher UX reviewed and improved
- [ ] Playtester-ready: install and play in <5 minutes

---

## Milestone 2: voxel_world Alpha

**Status**: Planned  
**Goal**: Complete first game demonstrating engine capabilities

### Planned Features

- **Gameplay Loop**: Exploration, resource gathering, basic progression
- **Biome Variety**: 8+ distinct biomes with unique terrain
- **Multiplayer**: Stable LAN play for 2-8 players
- **Content**: Sufficient blocks, items, and mechanics for 1+ hour of gameplay
- **Polish**: Smooth performance, intuitive controls, visual appeal

### Milestone 2 Success Criteria

- [ ] Playable alpha release for external playtesters
- [ ] Multiplayer stress-tested with 8 concurrent players
- [ ] Player feedback incorporated into iteration plan
- [ ] Game serves as reference implementation for engine

---

## Milestone 3: Visual Map Editor

**Status**: Planned  
**Goal**: Multiplayer collaborative world building tool

### Editor Features

- **POI-Based Design**: Points of interest with chunk-sized regions
- **Collaborative Editing**: Real-time multiplayer map building
- **Visual Tools**: Paint terrain, place entities, configure biomes
- **Export Pipeline**: Direct integration with world generation
- **Preview Mode**: Test gameplay without leaving editor

### Editor Success Criteria

- [ ] Functional editor with terrain painting
- [ ] Multiplayer sync for collaborative editing
- [ ] POI system integrated with world generation
- [ ] Beginner-friendly UX validated with new users

---

## Milestone 4: Customization Tools

**Status**: Planned  
**Goal**: Character and world personalization

### Customization Features

- **Character Skinning**: Texture and color customization
- **Primitive Modeling**: Build from cubes, spheres, etc.
- **Model Extension**: Add parts to existing models
- **Basic Rigging**: Custom animation support
- **Asset Sharing**: Export and import custom content

### Customization Success Criteria

- [ ] Visual character customization without code
- [ ] Custom assets usable in-game
- [ ] Community sharing pipeline established
- [ ] Beginner tutorials for customization workflow

---

## Long-Term Vision

### Editor & Tooling

- **Visual Level Editor**: Drag-and-drop world building
- **Asset Pipeline**: Import/export for models, textures, sounds
- **Debugging Tools**: In-game profiler, entity inspector
- **Build System**: One-click packaging for distribution

### Community Ecosystem

- **Game Gallery**: Showcase of MyCraft-powered games
- **Asset Marketplace**: Community-created content sharing
- **Tutorials & Courses**: Video series and written guides
- **Discord/Forums**: Active community support channels

### Technical Enhancements

- **Advanced Rendering**: Shaders, lighting, post-processing
- **Audio System**: 3D spatial audio and music
- **AI Framework**: Pathfinding, behavior trees, NPC systems
- **Optimization**: LOD system, chunk streaming, GPU acceleration

---

## Release Philosophy

### Versioning

- **Major versions** (1.0, 2.0): Breaking API changes, major features
- **Minor versions** (1.1, 1.2): New features, backward compatible
- **Patch versions** (1.1.1): Bug fixes, performance improvements

### Release Cadence

- **Milestone releases**: When success criteria met (no fixed timeline)
- **Sprint releases**: Every 2-4 weeks for active development
- **Hotfixes**: As needed for critical bugs

### Stability Guarantee

- Engine API stability prioritized after Milestone 2
- Deprecation warnings for 2 minor versions before removal
- Migration guides for breaking changes

---

## Contributing to the Roadmap

Have ideas for MyCraft's future? We welcome:

- **Feature proposals**: Open an issue with the `enhancement` label
- **Milestone feedback**: Comment on roadmap discussions
- **Implementation PRs**: See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

---

## Current Sprint

See [`docs/tech_debt.md`](docs/tech_debt.md) for:

- Active sprint goals (currently Sprint 5: Polish & UX)
- Detailed task breakdown
- Technical debt tracking
- Completed features and next steps

---

*Last Updated: 2025-12-20*  
*Version: 1.0*
