# MyCraft Game Design Document

**Version**: 1.0 (Hybrid Alpha Focus)
**Last Updated**: 2026-01-04
**Status**: Living Document

---

## 🌟 Executive Summary

**MyCraft** is an **exploration-driven action adventure** set in a procedural voxel world. It combines the freedom of a sandbox with the satisfaction of a momentum-based action game.

The current core loop (**v1.0-Hybrid Alpha**) focuses on **Social Color Combat**: players explore the world, fight enemies using timing and momentum, collect color swatches as loot, and use them to customize their avatar or interact playfully with friends.

> **Key Difference**: Unlike traditional sandboxes where you grind for materials to build, here you fight to express yourself. Building and "Weirdness" content are active future pillars but secondary to the immediate "Combat + Customization" loop.

---

## 🎮 Core Gameplay Loop (v1.0)

The "Color Combat Loop" drives the immediate player experience:

```
SPAWN → EXPLORE (Locate Camps) → FIGHT (Momentum Combat) → LOOT (Color Swatches) → CUSTOMIZE / SOCIALIZE
```

### 1. Combat & Movement

**Philosophy**: "Traverse with style, fight with momentum."

* **Momentum-Based Damage**: Damage output is scaled by player velocity.
  * *Standing still*: Base damage.
  * *Sprinting/Sliding/Falling*: Bonus damage multiplier.
  * *Goal*: Encourage aggressive movement, lunges, and aerial attacks rather than static button mashing.
* **Timing**: Dodge and Parry are key defensive mechanics.
* **Enemy Readability**:
  * **Tinting**: Enemies are visually tinted to indicate the color loot they drop (e.g., a Gold Skeleton drops Gold color).
  * **Tells**: Attacks have clear windups (1.5s - 2.0s) to allow for reactive dodging.

### 2. The Reward: Colors

Colors are the primary loot and currency of the Alpha.

* **Collect**: Defeating tinted enemies drops "Color Swatches".
* **Customize**: Apply colors immediately to your avatar (body parts or full presets).
* **Camp Seeding**: Enemy camps have deterministic color tables based on world seed (e.g., "The camp at North Ridge always has Teal").

### 3. Social Interaction

Multiplayer is not just seeing each other; it's interacting.

* **Trading**: Seamlessly swap duplicate colors with friends.
* **Color Projectiles**: Throw accumulated colors at other players to temporarily "paint" them (60s override). A playful, non-toxic social mechanic.
* **Visual Sync**: All customization and temporary effects are synced over the network in real-time.

---

## 🔮 Future Pillars (Post-v1.0)

These features are critical to the long-term vision but are **not** the focus of the current Alpha sprint.

### 1. Building & Hoarding (Target: v2.0 Beta)

* **Chunk-based Build Zones**: Players claim areas to build permanent bases.
* **Modular Construction**: Wall/Floor/Roof snapping system (Fallout-style).
* **Hoarding**: Physical storage for collected items and trophies.

### 2. "Weirdness" & Aesthetic Polish (Target: Content Updates)

* **Mash-up Aesthetic**: A blend of Voxel purity, Skyrim atmosphere, and Sci-Fi tech.
* **Examples**: Dragons with missile launchers, neon-fantasy biomes, and other genre-bending elements.
* **Status**: These are content polish goals for later versions once the engine foundation is solid.

---

## 🗺️ Roadmap Alignment

* **v0.x**: Engine Foundation (Done)
* **v1.0-Hybrid (Current)**: Color Combat Loop
  * *Focus*: Combat feel (Momentum), Enemy Tinting, Avatar Customization, Social Mechanics.
* **v2.0**: The Building Update
  * *Focus*: Base building, persistent world modification, economy.

---

*This document supersedes `VISION_VOXEL_WORLD.md`.*
