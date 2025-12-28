# VISUAL POLISH

## Phase 0 — Baseline Lock (Short, Surgical)

**Goal:** Freeze the rules of perception so nothing drifts later.

### Milestones

* Single lighting model locked (sun + ambient rules)
* Camera baseline defined (default FOV, lag, pitch limits)
* Player mannequin readability confirmed (already done)
* Visual palette bands defined (terrain, hazard, background)

**Exit Criteria**

* A single world seed looks intentional
* Visuals remain coherent when moving at max speed

---

# Phase 1 — State Authority & Movement Core (Highest ROI)

**Goal:** Establish a single source of truth for player and world behavior.

### Milestones

* Explicit player state model implemented

  * Grounded
  * Airborne
  * Falling
  * Sliding (if applicable)
  * Disabled / Dead
* Clear entry/exit rules for each state
* State-driven movement parameters

  * Acceleration
  * Max speed
  * Friction
  * Air control
* Input routing tied to state

**Exit Criteria**

* Player never exhibits ambiguous behavior
* Movement “feel” is consistent across sessions
* State can be logged and reasoned about deterministically

---

## Phase 2 — Animation & Camera as State Communication

**Goal:** Make states visible and legible without UI.

### Milestones

* Placeholder animations wired strictly to state transitions
* Key transitions implemented:

  * Idle → Move
  * Ground → Air
  * Air → Ground
  * Normal → Disabled
* Transition timing tuned (anticipation, impact, recovery)
* Camera behavior bound to player state (not raw velocity)

**Exit Criteria**

* Testers can infer state changes visually
* No animation plays “out of context”
* Camera reinforces traversal intent and depth

---

## Phase 3 — Terrain Semantics & World Readability

**Goal:** Terrain communicates traversal intent at a glance.

### Milestones

* Terrain traversal tags finalized:

  * Safe
  * Slow
  * Dangerous
  * Impassable
* Movement modifiers bound to terrain tags
* Visual encoding per tag:

  * Value range
  * Saturation
  * Light response
* Verticality clarity pass (lighting, faces, fade)

**Exit Criteria**

* Players guess terrain behavior correctly before interacting
* Height and depth are readable during motion
* No new geometry required to explain terrain rules

---

## Phase 4 — Feedback, Failure, and Trust

**Goal:** Replace polish with clarity.

### Milestones

* Centralized state-transition feedback system

  * Audio hooks
  * Camera impulses
  * Minimal particles (optional)
* Failure implemented as a state, not an event
* Fast, clean reset loop

**Exit Criteria**

* Cause of failure is always obvious
* No confusion about control loss or recovery
* Testers remain willing to retry after failure

---

## Phase 5 — Playtest Slice Packaging

**Goal:** Gather high-quality feedback, not noise.

### Milestones

* Fixed or constrained seed pool
* Short, focused traversal loop
* Disabled nonessential systems
* Tester-facing goals defined (what to evaluate)

**Exit Criteria**

* Playtest sessions are time-boxed and repeatable
* Feedback maps cleanly to movement, states, or readability
* No feedback is about “what am I supposed to do?”

---

## Timeline Characteristics (Intentionally)

* Front-loaded on systems, not content
* Every phase is shippable internally
* No phase assumes future art or PoI systems
* Nothing here creates rework debt

---

## One-Line Guiding Principle

> Each phase must reduce ambiguity before adding possibility.
