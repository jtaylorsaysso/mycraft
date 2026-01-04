# Animation Editor

**For Developers and Animators**

The Animation Editor is an in-engine tool for visually editing animation timing, events, and parameters without code changes. It is part of the standalone **Editor Suite**.

---

## Overview

The editor provides:

- **Visual timeline** with keyframe and event markers
- **Playback controls** (play/pause/stop/scrub)
- **Parameter sliders** (duration, looping)
- **Event management** (add/edit animation events)
- **JSON export/import** for version control

**Location**: `engine/editor/tools/animation_editor.py`

---

## Quick Start

### 1. Launch Editor Suite

Run the standalone editor application:

```bash
python -m engine.editor.app
```

### 2. Switch to Animation Editor

Click the "Animation" tab in the sidebar or press `2`.

### 3. Load an Animation

Click **📂 Load Clip** or select an existing one from the "Clip" dropdown if available.

### 4. Playback

- Click **▶ Play** to see the animation on the timeline.
- Use **◀ / ▶** buttons to step freely.

### 5. Edit Parameters

- Drag **Duration** slider to change length.
- Toggle **Looping** for cycle animations.

### 6. Save Changes

Click **💾 Save Clip** to export to `engine/assets/animations/<name>.json`.

---

## UI Components

### Clip Selector

**Function**: Selects the active animation clip from the `AnimationRegistry`.

- **(no clips)**: Default state when empty.

### Timeline Widget

**Visuals**:

- **Red Line**: Playhead (current time)
- **Green Diamonds**: Keyframes
- **Orange Lines**: Events

### Controls

- **Play/Pause/Stop**: Standard media controls.
- **Time Display**: Shows `current / total` time.

### Footer

- **Save Clip**: Opens a dialog to enter filename.
- **Load Clip**: Opens a dialog to enter filename to load.

---

## Integration Architecture

The Animation Editor is a tool within the `EditorApp` ecosystem.

### Class Structure

```python
class AnimationEditor:
    def __init__(self, app):
        self.app = app
        self.registry = app.anim_registry
        self.selection = None  # Shared selection state
        
    def show(self):
        # Build/Show UI
        
    def hide(self):
        # Hide UI, stop playback
```

### Shared Selection

It participates in the `EditorSelection` system. While primarily for timing, future updates will allow selecting bones in the Model Editor and seeing their keyframes highlighted here.

### Asset Management

Clip I/O is handled by `app.asset_manager`:

- **Load**: `app.asset_manager.load_animation_clip(filename)`
- **Save**: `app.asset_manager.save_animation_clip(clip, filename)`

---

## JSON Format

Animations are saved as JSON files in `engine/assets/animations/`.

```json
{
  "name": "attack_slash",
  "duration": 0.8,
  "looping": false,
  "keyframes": [
    {
      "time": 0.0,
      "transforms": { ... }
    }
  ],
  "events": [
    {
      "time": 0.4,
      "event_name": "hit_impact"
    }
  ]
}
```

---

## Planned Features

- **Event Editing**: Clicking event markers to change name/data.
- **Curve Editor**: Graph view for easing curves.
- **Box Select**: Moving multiple keyframes at once.
- **Scrubbing**: Dragging playhead on timeline (currently read-only viz).

---

*Last Updated: 2026-01-04*
