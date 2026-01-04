# Model Editor User Guide

The Model Editor is your tool for customizing voxel characters. It allows you to adjust bone positions, proportions, and poses to create unique avatars.

---

## Interface Overview

The editor is divided into three main areas:

1. **Viewport**: The 3D view of your character.
2. **Sidebar (Left)**: Tool selection and mode switching.
3. **Properties Panel (Right)**: Fine-tuning for the selected bone.

---

## Getting Started

To launch the editor, select the "Model Editor" tab from the main Editor Suite interface.

### Navigation

- **Right Click + Drag**: Rotate camera
- **Middle Click + Drag**: Pan camera
- **Wheel**: Zoom in/out

---

## Editing Modes

### 1. Normal Mode (Bone Editing)

This is the default mode for adjusting skeletal proportions.

- **Select a Bone**: Click on any blue box (bone visual) to select it.
- **Move**: Drag the Gizmo arrows to change the bone's length/position.
- **Rotate**: Drag the Gizmo rings to change orientation.

> [!TIP]
> Use **Symmetry Mode** (`S` key) to mirror changes from Left <-> Right automatically!

### 2. Spine Mode

Activated by the "Spine Mode" toggle or `M` key.

- Used for adjusting the spinal curve.
- Manipulate control points to bend the character's back naturally.
- Useful for hunched creatures or distinct postures.

---

## Key Features

### Symmetry (`S`)

When enabled, moving the `Left Arm` will automatically update the `Right Arm`. Always keep this on for symmetrical characters.

### Undo/Redo (`Ctrl+Z` / `Ctrl+Y`)

Made a mistake? Rapidly step back through your changes.

### Reset Bone

If a bone gets messed up, select it and click "Reset Bone" in the properties panel to return it to the default T-Pose.

---

## Saving & Loading

- **Save**: Exports your avatar configuration to a JSON file.
- **Load**: Imports a previously saved JSON file.

Files are saved to `engine/assets/avatars/`.

---

## Shortcuts Reference

| Key | Action |
|:--|:--|
| `1` | Switch to Select Tool |
| `2` | Switch to Move Tool |
| `3` | Switch to Rotate Tool |
| `S` | Toggle Symmetry |
| `M` | Toggle Spine Mode |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Esc` | Deselect All |

---

*Last Updated: 2026-01-04*
