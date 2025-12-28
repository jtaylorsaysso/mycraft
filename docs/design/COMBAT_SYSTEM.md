# Combat System Design

**Status**: In Progress (Milestone 2)  
**Last Updated**: 2025-12-28

This document outlines the design and architecture for the **voxel_world** combat system, focusing on timing, momentum, and stamina management.

---

## Core Philosophy

> **"Traversal is gameplay, combat is momentum."**

1. **Timing-Based**: Skill is determined by reaction and prediction, not just stats.
2. **Momentum Integration**: Movement speed directly impacts damage output.
3. **Stamina Management**: Vital resource for both defense (dodge/parry) and traversal.
4. **Readable Challenges**: Enemies have clear visual/audio tells.

---

## Mechanics

### 1. Stamina System

A unified resource for all physical actions.

- **Regeneration**: 20/sec (starts after 0.5s delay)
- **Max Stamina**: 100 (default)

**Costs:**

| Action | Cost | Notes |
| :--- | :--- | :--- |
| **Sprint** | 10/sec | Traversal |
| **Climb** | 15/sec | Traversal |
| **Swim** | 5/sec | Traversal |
| **Vault** | 10 flat | Traversal |
| **Dodge** | 15-35 | Scaled by timing (Combat) |
| **Parry** | 5-20 | Scaled by timing (Combat) |

### 2. Defensive Actions

**Dodge (Shift)**

- **Effect**: Positional roll + I-frames (0.3s)
- **Commitment**: High interaction, breaks combat flow to reposition
- **Perfect Timing**: 15 stamina
- **Good Timing**: 20 stamina
- **Bad Timing**: 30 stamina
- **Failed Timing**: 30 stamina, damage taken

**Parry (Mouse 2)**

- **Effect**: Damage mitigation (no movement)
- **Commitment**: Stand your ground
- **Perfect Timing**: 100% mitigation, 5 stamina
- **Good Timing**: 70% mitigation, 10 stamina
- **Bad Timing**: 30% mitigation, 15 stamina
- **Failed Timing**: 0% mitigation, 20 stamina

### 3. Offensive Actions

**Primary Attack (Mouse 1)**

- **Animation**: 0.5s duration
- **Hit Window**: 0.12s - 0.18s
- **Cancel Window**: After 0.35s (Medium commitment)
- **Damage Formula**:

    ```python
    damage = (base_damage + player_velocity_magnitude) * multiplier
    ```

**Multipliers**:

- Backstab / Flanking
- Enemy Stun State

### 4. Enemy Design: The Skeleton

**Archetype**: Telegraphed Attacker

- **Health**: 50
- **Damage**: 20
- **AI State Machine**:
    1. **Idle**: Scan range (10 units)
    2. **Aggro**: Move to range (2.5 units)
    3. **Windup**: 1.5s telegraph (Visual + Audio)
    4. **Attack**: 0.3s damage window
    5. **Recovery**: 2.0s vulnerable window

---

## Technical Architecture

### Engine Layer

- **`Stamina` Component**: Generic resource data.
- **`Health` Component**: Existing life/invulnerability.
- **`DamageSystem`**: Handles damage events and death.

### Game Layer (`voxel_world`)

- **`StaminaSystem`**: Handles regen and drain logic.
- **`DodgeSystem`**: Handles input, costs, and i-frames.
- **`ParrySystem`**: Intercepts damage events for mitigation.
- **`CombatSystem`**: Handles attack state, hit detection, and friendly fire.
- **`SkeletonAISystem`**: Drives enemy behavior.

---

## Configuration

**Friendly Fire**

- Host configurable on world creation.
- Values: 0.0 (Off), 0.5 (Half), 1.0 (Full).

---

## Implementation Plan

See [Task List](../../.gemini/antigravity/brain/88f9291f-1d0b-4ec1-80ef-2e8d862cb0e8/task.md) for detailed breakdown.
