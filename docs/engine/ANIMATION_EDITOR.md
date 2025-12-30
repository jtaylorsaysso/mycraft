# Animation Editor

**For Developers and Animators**

The Animation Editor is an in-engine tool for visually editing animation timing, events, and parameters without code changes. Perfect for tuning combat animations and hit windows.

---

## Overview

The editor provides:

- **Visual timeline** with keyframe and event markers
- **Playback controls** (play/pause/stop/scrub)
- **Parameter sliders** (duration, looping)
- **Event management** (add/edit animation events)
- **JSON export/import** for version control

**Access**: Press **F4** to toggle (after integration)

---

## Quick Start

### 1. Open Editor

Press `F4` in-game to open the animation editor window.

### 2. Select Animation

Use the dropdown to select an animation clip (e.g., `attack_light`, `walk`, `dodge_forward`).

### 3. Play Animation

Click **▶ Play** to see the animation on the timeline. The red playhead shows current time.

### 4. Adjust Parameters

- Drag **Duration** slider to change animation length
- Toggle **Looping** checkbox for cycle animations
- Scrub timeline by clicking **◀/▶** step buttons

### 5. Save Changes

Click **💾 Save to JSON** to export the modified animation to `data/animations/<clip_name>.json`.

### 6. Reload

Click **🔄 Reload** to refresh the clip from JSON (discards unsaved changes).

---

## UI Components

### Clip Selector

![Clip selector dropdown showing available animations]

**Location**: Top of editor window  
**Function**: Populate from `AnimationRegistry`, load clip on selection

---

### Playback Controls

![Playback controls with play/pause/stop/step buttons]

**Buttons**:

- **▶ Play**: Start playback, updates timeline in real-time
- **⏸ Pause**: Pause playback, maintains current time
- **⏹ Stop**: Stop playback, reset to 0.0s
- **◀**: Step backward ~1 frame (0.016s)
- **▶**: Step forward ~1 frame (0.016s)

**Time Display**: Shows `current_time / duration` (e.g., `0.25s / 0.50s`)

---

### Timeline Widget

![Timeline with keyframe markers (green diamonds) and event markers (orange lines)]

**Features**:

- **Time ruler**: Tick marks every 0.1s, labeled every 0.5s
- **Keyframe markers**: Green diamonds at keyframe times
- **Event markers**: Orange vertical lines with event names
- **Playhead**: Red vertical line showing current time

**Interaction** (planned):

- Click timeline to seek to time
- Drag playhead to scrub

---

### Parameter Panel

![Parameter sliders for duration and looping checkbox]

**Controls**:

- **Duration (s)**: Slider (0.1s - 5.0s), updates clip duration
- **Looping**: Checkbox, toggles clip looping

**Live Updates**: Changes apply immediately to clip

---

### Event Editor

![Event list and "Add Event" button]

**Controls**:

- **Event count**: Display (e.g., "3 events")
- **+ Add Event**: Creates new event at current play head time

**Planned**:

- Event list with edit/delete buttons
- Event name and data fields

---

### Footer

![Save/Reload buttons and F4 close hint]

**Buttons**:

- **💾 Save to JSON**: Export clip to `data/animations/<clip_name>.json`
- **🔄 Reload**: Reload clip from JSON file

**Hint**: "Press F4 to Close"

---

## Animation Registry

The `AnimationRegistry` manages all animation clips in the engine.

### Registration

```python
from engine.animation.animation_registry import get_animation_registry

registry = get_animation_registry()

# Register procedural clip
walk_clip = create_walk_cycle(duration=1.0)
registry.register_clip(walk_clip)

# Register combat clip
slash_clip = create_sword_slash()
registry.register_combat_clip(slash_clip)
```

### Listing Clips

```python
# Get all clip names
all_clips = registry.list_clips()  # ['walk', 'attack_light', 'dodge_forward', ...]

# Get combat clip names only
combat_clips = registry.list_combat_clips()  # ['attack_light', 'dodge_forward', ...]
```

### Retrieving Clips

```python
# Get clip by name
clip = registry.get_clip('attack_light')

# Get combat clip with metadata
combat_clip = registry.get_combat_clip('attack_light')
print(combat_clip.hit_windows)  # [HitWindow(start=0.12, end=0.18, damage_mult=1.0)]
```

---

## JSON Workflow

### Save to JSON

```python
from pathlib import Path

# Save clip to JSON
output_path = Path('data/animations/attack_light.json')
registry.save_to_json('attack_light', output_path)
```

**Output** (`attack_light.json`):

```json
{
  "name": "attack_light",
  "duration": 0.5,
  "looping": false,
  "keyframes": [
    {
      "time": 0.0,
      "transforms": {
        "upper_arm_right": {
          "position": [0, 0, 0],
          "rotation": [0, -90, 0],
          "scale": [1, 1, 1]
        }
      }
    }
  ],
  "events": [
    {"time": 0.12, "event_name": "hit_start", "data": {}},
    {"time": 0.15, "event_name": "impact", "data": {}},
    {"time": 0.18, "event_name": "hit_end", "data": {}}
  ],
  "combat_metadata": {
    "hit_windows": [{"start_time": 0.12, "end_time": 0.18, "damage_multiplier": 1.0}],
    "can_cancel_after": 0.35,
    "momentum_influence": 0.4,
    "recovery_time": 0.15
  }
}
```

### Load from JSON

```python
# Load single file
json_path = Path('data/animations/attack_light.json')
clip = registry.load_from_json(json_path)

# Or reload and register
registry.reload_from_json(json_path)
```

### Scan Directory

```python
# Load all animations from directory
animations_dir = Path('data/animations')
registry.scan_directory(animations_dir)

# Now all JSON clips are registered
print(registry.list_clips())
```

---

## Integration Steps

### 1. Initialize Registry

In `VoxelGame.__init__()`:

```python
from engine.animation.animation_registry import get_animation_registry
from engine.animation.combat import create_sword_slash, create_dodge_forward

# Get global registry
self.anim_registry = get_animation_registry()

# Register procedural clips
self.anim_registry.register_combat_clip(create_sword_slash())
self.anim_registry.register_combat_clip(create_dodge_forward())

# Scan for JSON clips
animations_dir = Path('data/animations')
if animations_dir.exists():
    self.anim_registry.scan_directory(animations_dir)
```

### 2. Create Editor Window

```python
from engine.ui.animation_editor import AnimationEditorWindow

# Create editor (after ShowBase initialization)
self.anim_editor = AnimationEditorWindow(self.base, self.anim_registry)
```

### 3. Add F4 Toggle

In `InputManager` or `PlayerControlSystem`:

```python
# Register F4 key
self.base.accept('f4', self._toggle_anim_editor)

def _toggle_anim_editor(self):
    if hasattr(self.base, 'anim_editor'):
        self.base.anim_editor.toggle()
```

### 4. Create Data Directory

```bash
mkdir -p data/animations
```

---

## Timeline Widget API

### Creating a Timeline

```python
from engine.ui.timeline_widget import TimelineWidget

timeline = TimelineWidget(
    parent=self.frame,  # DirectGUI parent
    x=-1.0,  # Normalized screen X
    y=0.15,  # Normalized screen Y
    width=2.0,  # Normalized width
    height=0.2,  # Normalized height
    duration=1.0  # Animation duration
)
```

### Adding Markers

```python
# Add keyframe marker (green diamond)
timeline.add_keyframe_marker(time=0.5, bone="upper_arm_right")

# Add event marker (orange line + label)
timeline.add_event_marker(time=0.12, event_name="hit_start")
```

### Updating Playhead

```python
# Set playhead position
timeline.set_playhead(time=0.25)  # 0.25s
```

### Clearing Markers

```python
# Remove all markers (e.g., when loading new clip)
timeline.clear_markers()
```

### Changing Duration

```python
# Update timeline duration (rebuilds ruler)
timeline.set_duration(duration=2.0)
```

---

## Editor Window API

### Creating the Editor

```python
from engine.ui.animation_editor import AnimationEditorWindow
from engine.animation.animation_registry import AnimationRegistry

registry = AnimationRegistry()
editor = AnimationEditorWindow(base, registry)
```

### Showing/Hiding

```python
# Show editor
editor.show()

# Hide editor
editor.hide()

# Toggle visibility
editor.toggle()
```

### Loading a Clip

```python
# Load clip by name
editor.load_clip('attack_light')

# Timeline updates automatically
# Parameters populate from clip
```

### Playback Control

```python
# Start playback
editor._on_play()

# Pause
editor._on_pause()

# Stop (reset to 0)
editor._on_stop()

# Step forward/backward
editor._step_frame(0.016)   # +1 frame
editor._step_frame(-0.016)  # -1 frame
```

**Note**: Internal methods prefixed with `_` may change. Use UI buttons in practice.

---

## Keyboard Shortcuts (Planned)

| Key | Action |
|:--|:--|
| `F4` | Toggle editor |
| `Space` | Play/Pause |
| `Left Arrow` | Step backward |
| `Right Arrow` | Step forward |
| `Home` | Jump to start |
| `End` | Jump to end |
| `Ctrl+S` | Save to JSON |
| `Ctrl+R` | Reload from JSON |

---

## Workflow Examples

### Tuning Combat Hit Windows

**Goal**: Adjust `attack_light` hit window to match visual sword swing.

1. Press `F4` to open editor
2. Select `attack_light` from dropdown
3. Click **▶ Play** to watch animation
4. Note visual swing occurs at ~0.14s (not 0.12s)
5. Click **+ Add Event** at 0.14s to create new `impact` marker
6. Delete old 0.15s `impact` event (planned feature)
7. Adjust duration slider if attack feels too slow/fast
8. Click **💾 Save to JSON**
9. Reload game to see changes

### Creating New Animation from JSON

1. Copy existing JSON (e.g., `attack_light.json` → `attack_heavy.json`)
2. Edit JSON:
   - Change `name` to `"attack_heavy"`
   - Increase `duration` to `0.8`
   - Adjust keyframe times proportionally
   - Add longer hit window
3. Save to `data/animations/attack_heavy.json`
4. In game, registry automatically scans directory on startup
5. `attack_heavy` appears in editor dropdown

### Version Control Workflow

```bash
# 1. Make changes in editor
# 2. Save to JSON
# 3. Commit JSON files
git add data/animations/*.json
git commit -m "Tune attack timings for better feel"

# 4. Share with team
git push

# 5. Teammates pull and reload
git pull
# Restart game, changes auto-load from JSON
```

---

## Known Limitations

### Current (v1.0)

- ❌ No click-to-seek on timeline
- ❌ Cannot edit event names or data
- ❌ No combat-specific parameter sliders (hit windows, cancel window)
- ❌ No undo/redo
- ❌ No preview viewport (mannequin playback)
- ❌ No curve visualization

### Planned (Future Releases)

- ✅ Click timeline to seek
- ✅ Event editing UI (name, data fields)
- ✅ Hit window sliders with visual overlay
- ✅ Isolated preview mannequin
- ✅ Bone rotation curve graphs (read-only)
- ⚠️ Tangent handle editing (low priority)

---

## Troubleshooting

### Editor doesn't open (F4)

**Check**:

1. Is `AnimationEditorWindow` created in `VoxelGame.__init__()`?
2. Is F4 binding registered in `InputManager`?
3. Any errors in console?

**Debug**:

```python
print(hasattr(self.base, 'anim_editor'))  # Should be True
self.base.anim_editor.show()  # Test direct show
```

---

### Clip not in dropdown

**Check**:

1. Is clip registered in `AnimationRegistry`?
2. Did you call `registry.scan_directory()` if loading from JSON?

**Debug**:

```python
registry = get_animation_registry()
print(registry.list_clips())  # Should include your clip
```

---

### Changes don't persist

**Check**:

1. Did you click **💾 Save to JSON**?
2. Does `data/animations/` directory exist?
3. Are you reloading the JSON on game restart?

**Debug**:

```bash
ls data/animations/  # Check for .json files
cat data/animations/attack_light.json  # Verify saved changes
```

---

### Timeline markers missing

**Check**:

1. Did clip load successfully?
2. Are keyframes/events defined in clip?

**Debug**:

```python
clip = registry.get_clip('attack_light')
print(f"Keyframes: {len(clip.keyframes)}")
print(f"Events: {len(clip.events)}")
```

---

## Performance

### Target Metrics

- **Editor open**: <50ms
- **Clip load**: <10ms
- **Playback update**: <1ms per frame
- **Save to JSON**: <20ms

**Bottlenecks**: DirectGUI widget creation (one-time cost).

---

## Related Documentation

- [Animation System](ANIMATION_SYSTEM.md) - How animations work
- [Combat Architecture](COMBAT_ARCHITECTURE.md) - Hit window integration
- [Player Mechanics](player_mechanics.md) - AnimationMechanic

---

*Last Updated: 2025-12-30*  
*Version: 1.0*
