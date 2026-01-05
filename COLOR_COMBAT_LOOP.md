# Color Combat Loop Design

**Last Updated**: 2026-01-03  
**Status**: Active Design (v1.0-Hybrid Alpha)

---

## Philosophy

> **Colors aren't just cosmetics—they're toys.**

The Color Combat Loop integrates avatar customization directly into gameplay as a reward system and social mechanic. Players see enemies, identify their value by color tint, defeat them for loot, and use that loot to customize themselves OR playfully interact with friends.

---

## Core Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│                    THE COLOR LOOP                                    │
│                                                                      │
│   See Tinted Enemy → Fight → Collect Swatch → Choose:               │
│                                                   │                  │
│                     ┌─────────────┬──────────────┼──────────────┐   │
│                     ▼             ▼              ▼              ▼   │
│                Apply to Self   Trade to     Throw at Friend   Save  │
│                               Teammate     (60s override!)          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### 1. Visual Clarity

**Enemy tinting signals loot before engagement.**

- Gold-tinted zombie → Player knows it drops gold color
- Red-tinted skeleton → Crimson color drop
- Mixed camp → Visual variety = loot variety

**Why It Works**:

- Players make informed risk/reward decisions
- Farming specific colors is intentional, not random
- Groups can coordinate: "I'll take the gold one!"

---

### 2. Social Playfulness

**Colors enable player-to-player interaction.**

| Mechanic | Intent | Experience |
|----------|--------|------------|
| **Trading** | Cooperation | "Here's the blue you wanted!" |
| **Throwing** | Playful chaos | "You're pink now for 60 seconds!" |
| **Showing off** | Pride | "Check out my Knight preset!" |

**Why It Works**:

- Low-stakes social interaction
- Encourages communication and laughter
- Memorable multiplayer moments

---

### 3. Integrated Progression

**Customization IS the reward, not an afterthought.**

Traditional structure:

```
Fight Enemy → Get XP/Gold → Buy Cosmetic (separate shop)
```

Color Combat Loop:

```
Fight Enemy → Get Color → Customize Immediately
```

**Why It Works**:

- Immediate gratification (no shop UI intermediary)
- Direct link between combat and customization
- Loot feels meaningful (not just currency)

---

## Systems

### Color Palette

#### Starter Colors (8)

Available immediately at game start:

| Color | RGBA | Purpose |
|-------|------|---------|
| Red | `(0.9, 0.2, 0.2, 1.0)` | Primary |
| Blue | `(0.2, 0.4, 0.9, 1.0)` | Primary |
| Yellow | `(0.9, 0.9, 0.2, 1.0)` | Primary |
| Green | `(0.2, 0.8, 0.2, 1.0)` | Secondary |
| Orange | `(0.9, 0.5, 0.1, 1.0)` | Secondary |
| Purple | `(0.6, 0.2, 0.8, 1.0)` | Secondary |
| White | `(0.9, 0.9, 0.9, 1.0)` | Neutral |
| Black | `(0.15, 0.15, 0.15, 1.0)` | Neutral |

#### Loot Colors (Extended Palette)

Dropped by enemies, unlockable through gameplay:

- **Rare Hues**: Crimson, Navy, Gold, Silver
- **Natural**: Forest, Coral, Teal
- **Metallics**: Bronze, Charcoal
- **Soft**: Lavender, Peach, Mint
- **More to be added**

---

### Enemy Tinting

#### Tint System

```python
# Blend enemy base color with loot color
visual_color = blend(base_color, loot_color, tint_strength)

# Tint strength varies by enemy type
skeleton_tint = 0.4  # Subtle (bone shows through)
zombie_tint = 0.6    # Strong (decayed flesh holds color)
```

#### Visual Examples

| Enemy | Base | Loot | Result |
|-------|------|------|--------|
| Skeleton | Bone-white | Gold | Pale golden shimmer |
| Zombie | Gray-green | Crimson | Deep red-brown decay |
| Skeleton | Bone-white | Teal | Pale blue-green bones |

---

### Momentum Combat

**Movement is power.**

- **Velocity Scaling**: Attacks deal more damage when moving fast.
- **Technique**: Slide-attacks, aerial lunges, and sprinting strikes are optimal.
- **Defense**: Dodge and Parry are available, but spacing (using movement) is primary.

---

### Camp Seeding

#### Deterministic Color Distribution

```python
# Same camp = same colors in a world
camp_seed = hash(world_seed + camp_position)
rng = random.Random(camp_seed)

# Each camp has 2-4 colors
camp_colors = rng.sample(LOOT_COLORS, num=randint(2, 4))
```

**Player Experience**:

- Visit Camp A → Always red/gold/teal enemies (in this world)
- Different world → Same camp has different colors
- Share coordinates: "Camp at (100, 200) has crimson!"
- Farmable for specific colors

---

### Avatar Customization

#### Layers

1. **Body Color**: Default tint for all bones
2. **Per-Bone Colors**: Override specific limbs
3. **Presets**: Pre-defined full looks
4. **Temporary Override**: Thrown color (60s duration)

#### Effective Color Priority

```
if temporary_color and timer > 0:
    display temporary_color
else if bone in bone_colors:
    display bone_colors[bone]
else:
    display body_color
```

---

### Projectile System

#### Color Throw Mechanics

| Property | Value | Rationale |
|----------|-------|-----------|
| Cooldown | 3 seconds | Prevent spam, allow playful bursts |
| Duration | 60 seconds | Long enough to be funny, short enough to not annoy |
| Inventory cost | None | Non-depleting = always available for fun |
| Range | ~15 units | Generous for casual aiming |
| Target | Players only | Social mechanic, not combat |

#### Reusable Foundation

The projectile system is designed for future expansion:

- `engine/projectiles/base.py`: Physics, collision, lifetime
- `engine/projectiles/color_projectile.py`: Color-specific behavior
- Future: Combat projectiles, throwable items, magic spells

---

### Trading System

#### Flow

```
Player A looks at Player B → Press G (Offer)
    ↓
Player B sees prompt: "[Player A] offers [Crimson Swatch]"
    ↓
Player B presses Y (Accept) or N (Decline)
    ↓
If accepted: Swatch added to Player B's unlocked colors
```

#### Design Notes

- Max distance: 5 units (must be close)
- Offer expires: 30 seconds
- UI feedback: Clear prompts and confirmation

---

### POI Preset Rewards

#### Shrine Completion

**Challenge → Preset Unlock**

| Shrine Type | Preset | Visual Theme |
|-------------|--------|--------------|
| Combat | Knight | Steel armor, gold helmet |
| Exploration | Ranger | Forest green, brown hood |
| Puzzle | Mage | Purple robes, glowing hands |

**Why Presets Matter**:

- Instant full look (no per-bone customization needed)
- Achievement reward (feels special)
- Inspiration for color combinations

---

## Player Types

### The Collector

**"I want ALL the colors!"**

- Farms specific camps for rare colors
- Shares coordinates with friends
- Trades duplicates actively

### The Fashionista

**"I want to look COOL!"**

- Spends time in customization UI
- Unlocks presets from shrines
- Shows off unique combinations

### The Trickster

**"Let's paint each other!"**

- Uses color projectiles constantly
- Targets friends for laughs
- Creates chaos in multiplayer

### The Fighter

**"Colors are cool, but I'm here for combat!"**

- Collects colors passively
- Uses starter palette
- Focuses on combat skill

**All types are valid and supported.**

---

## Success Metrics

### Engagement

- [ ] Players identify enemy loot by tint within first 5 minutes
- [ ] 80%+ of players customize avatar in first session
- [ ] Color projectiles used at least once per 10-minute session
- [ ] Trading occurs naturally in multiplayer (no prompting)

### Fun Factor

- [ ] Playtesters laugh when painted by friends
- [ ] Players share camp coordinates in chat
- [ ] "One more color" keeps players engaged
- [ ] Preset unlocks feel rewarding

### Technical

- [ ] Enemy tinting performs at 60 FPS
- [ ] Network sync handles 4 players with frequent color changes
- [ ] No exploits for unlimited color throws
- [ ] Projectile system is reusable for future features

---

*Design Document — v1.0-Hybrid Alpha — 2026-01-03*
