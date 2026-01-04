# Animation Strategy & Architecture

## Executive Summary

This document outlines the strategic direction for the animation system, focusing on State Management (FSM) and Event Handling. Research into Panda3D conventions and general game development patterns suggests moving from ad-hoc state checks to a formal Finite State Machine (FSM) architecture for animation controllers.

## 1. State Management: The Move to FSMs

### Current State

Currently, `ProceduralAnimationSource` and `CombatAnimationSource` manage state via ad-hoc boolean flags and conditionals (e.g., `if is_walking: ...`, `if blend_timer < duration: ...`). This "Implicit State Machine" pattern is:

- **Fragile**: Hard to verify all transitions are valid.
- **Complex**: Blending logic is scattered across update loops.
- **Hard to Scale**: Adding new states (e.g., "Swimming", "Climbing") requires touching every conditional.

### Recommendation: `direct.fsm.FSM`

Panda3D provides a robust `direct.fsm.FSM` class. We should adopt this pattern for our Animation Sources.

**Proposed Architecture:**

```python
from direct.fsm.FSM import FSM

class LocomotionFSM(FSM):
    def __init__(self, source):
        FSM.__init__(self, "Locomotion")
        self.source = source
        
    def enterIdle(self):
        self.source.play("idle", loop=True)
        
    def enterWalk(self):
        self.source.play("walk", loop=True)
        
    def enterJump(self):
        self.source.play("jump", loop=False)
```

**Benefits:**

- **Encapsulation**: State-specific logic lives in `enter/exit` methods.
- **Validation**: FSMs can prevent invalid transitions (e.g., strict graph).
- **Debuggability**: FSMs naturally print state changes/transitions.

## 2. Event Management

### Current State

`VoxelAnimator` iterates a list of `AnimationEvent` objects attached to clips. On optimization (implemented recently), it checks time ranges efficiently.

- **Type**: Polling / Callback-based.
- **Scope**: Local to the Animator instance.

### Recommendation: Hybrid Event System

1. **Keep `VoxelAnimator` Events**: For tightly coupled logic (e.g., changing hitboxes during an attack), the current direct callback system is high-performance and explicitly synchronous.
2. **Add Messenger Integration**: For decoupled logic (e.g., UI updates, Sound effects), we should allow events to dispatch to Panda3D's global `messenger`.

**Implementation Pattern:**

```python
# VoxelAnimator event handler
def _trigger_event(self, event):
    # 1. Direct Callback (High Speed, Logic)
    if self.on_event:
        self.on_event(event)

    # 2. Global Message (Decoupled, Audio/VFX)
    # Event name: "AnimEvent-Footstep"
    messenger.send(f"AnimEvent-{event.name}", [event.data])
```

## 3. Editor Integration

The Editor must treat the FSM as the "Source of Truth".

- **Visualizing State**: The Editor should eventually visualize the FSM current state (e.g., "Current State: Walk").
- **Forcing Transitions**: Debug controls to manually call `fsm.request('Jump')`.

## Action Plan

1. **Refactor `ProceduralAnimationSource`**: Convert ad-hoc logic to `LocomotionFSM`.
2. **Refactor `CombatAnimationSource`**: Convert to `CombatFSM` (handling Combo windows via state transitions).
3. **Enhance `VoxelAnimator`**: Add optional `messenger.send` support for events.
