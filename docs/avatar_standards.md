# PlayerAvatar Model Standards

## Overview

The `VoxelAvatar` is the standard player character model in MyCraft. It uses a procedurally-generated voxel mesh driven by a `HumanoidSkeleton` with 18 bones arranged in a hierarchical structure.

This document defines the canonical avatar standards to ensure consistency as systems evolve and to support future customization features.

## Skeleton Structure

### Canonical Bone List

The `HumanoidSkeleton` contains exactly **18 bones**:

```
hips (root)
├── spine
│   ├── chest
│   │   ├── head
│   │   ├── shoulder_left
│   │   │   ├── upper_arm_left
│   │   │   │   ├── forearm_left
│   │   │   │   │   └── hand_left
│   │   └── shoulder_right
│   │       ├── upper_arm_right
│   │       │   ├── forearm_right
│   │       │   │   └── hand_right
├── thigh_left
│   ├── shin_left
│   │   └── foot_left
└── thigh_right
    ├── shin_right
        └── foot_right
```

### Bone Naming Conventions

- **Root bone**: Always `"hips"`
- **Spine chain**: `spine → chest → head`
- **Arms**: `shoulder_{side} → upper_arm_{side} → forearm_{side} → hand_{side}`
- **Legs**: `thigh_{side} → shin_{side} → foot_{side}`
- **Side suffix**: `_left` or `_right`

> [!IMPORTANT]
> All bone names must match `HumanoidSkeleton.EXPECTED_BONE_NAMES` exactly for validation to pass.

### Bone Length Standards

Visual geometry is created for bones with `length > 0.01`. Bones representing visual segments (pelvis, limbs, head) must have non-zero lengths.

| Bone | Length (Voxel Units) | Purpose |
|------|----------------------|---------|
| hips | 0.20 | Pelvic block (Root) |
| spine | 0.30 | Lower torso segment |
| chest | 0.30 | Upper torso / ribcage |
| head | 0.25 | Cranium block |
| shoulder | 0.15 | Shoulder pivot |
| upper_arm | 0.35 | Upper limb segment |
| forearm | 0.35 | Lower limb segment |
| hand | 0.15 | Extremity segment |
| thigh | 0.45 | Upper leg segment |
| shin | 0.45 | Lower leg segment |
| foot | 0.20 | Extremity segment |

> [!IMPORTANT]
> The **hips** bone is the root of the hierarchy and must have a non-zero length to ensure the pelvic cube is rendered. It is typically oriented to point **Up** (+Z in world-space T-pose).

## Runtime Validation

### Automatic Validation

By default, `VoxelAvatar` validates the skeleton on initialization:

```python
# Validation enabled (default)
avatar = VoxelAvatar(parent_node, skeleton)

# Explicit validation
avatar = VoxelAvatar(parent_node, skeleton, validate=True)
```

**What is validated:**

- ✅ All 18 expected bones exist
- ✅ No unexpected extra bones
- ✅ Correct bone hierarchy (spine, arm, leg chains)
- ✅ Joint constraints properly configured (elbows, knees)
- ✅ Thickness values defined for all bones

### Foot and Hand Orientation

In the default T-pose:

- **Arms** extend along World +/- X.
- **Legs** extend along World -Z (Down).
- **Feet** must rotate at the ankle to point **Forward** (World +Y).
- **Hands** typically point along the arm (World +/- X).

> [!NOTE]
> Since the `shin` bone points Down, the `foot` local rotation must be adjusted (e.g., Pitch 90) to point Forward relative to its parent.

### Opt-Out for Testing

Validation can be disabled for prototyping or testing:

```python
# Validation disabled
avatar = VoxelAvatar(parent_node, skeleton, validate=False)
```

> [!CAUTION]
> Only disable validation during development/testing. Production code should always validate to catch configuration errors early.

### Manual Validation

You can manually validate an avatar after construction:

```python
avatar = VoxelAvatar(parent_node, skeleton, validate=False)

# ... modify skeleton ...

# Manually validate
try:
    avatar.validate_avatar()
    print("✅ Avatar is valid")
except ValueError as e:
    print(f"❌ Validation error: {e}")
```

## Visual Standards

### Bone Thickness Map

Each bone has a standardized thickness value for consistent visual appearance:

```python
VoxelAvatar.BONE_THICKNESS_MAP = {
    "spine": 0.25,
    "chest": 0.35,
    "head": 0.25,
    "hips": 0.30,
    "thigh_left": 0.18,
    "thigh_right": 0.18,
    "shin_left": 0.15,
    "shin_right": 0.15,
    "upper_arm_left": 0.12,
    "upper_arm_right": 0.12,
    "forearm_left": 0.10,
    "forearm_right": 0.10,
    "shoulder_left": 0.15,
    "shoulder_right": 0.15,
    "hand_left": 0.08,
    "hand_right": 0.08,
    "foot_left": 0.12,
    "foot_right": 0.12,
}
```

Bones not in the map default to `0.1` thickness with a warning.

### Thickness Guidelines

- **Core body** (hips, spine, chest): 0.25-0.35
- **Head**: 0.25
- **Limbs (upper)**: 0.12-0.18
- **Limbs (lower)**: 0.10-0.15
- **Extremities** (hands, feet): 0.08-0.12

## Joint Constraints

### Elbow Constraints

Elbows can only bend forward (0° to 150° pitch):

```python
BoneConstraints(min_p=0, max_p=150)
```

### Knee Constraints

Knees can only bend backward (-150° to 0° pitch):

```python
BoneConstraints(min_p=-150, max_p=0)
```

### Head Constraints

Limited range of motion to prevent unnatural bending:

```python
BoneConstraints(
    min_p=-45, max_p=45,  # Pitch: nod up/down
    min_h=-60, max_h=60   # Heading: turn left/right
)
```

## Future Customization

### Planned Features

The standardized avatar structure supports future features:

1. **User Customization**
   - Custom body colors
   - Adjustable proportions (within validated ranges)
   - Accessory attachment points

2. **Developer Extensions**
   - Custom skeleton variants (must pass validation)
   - Additional bones for equipment/props
   - Procedural animation variations

### Extending the Avatar

To create custom avatar variants:

1. **Subclass `HumanoidSkeleton`** if you need different bone structure
2. **Override `EXPECTED_BONE_NAMES`** to define required bones
3. **Implement `validate_structure()`** for custom validation rules
4. **Update `BONE_THICKNESS_MAP`** in `VoxelAvatar` for custom bones

Example:

```python
class CustomSkeleton(HumanoidSkeleton):
    EXPECTED_BONE_NAMES = HumanoidSkeleton.EXPECTED_BONE_NAMES + ["tail"]
    
    def __init__(self):
        super().__init__()
        self.add_bone("tail", "hips", length=0.4)
```

## Testing

### Validation Tests

Run avatar validation tests:

```bash
python -m pytest tests/test_voxel_avatar.py tests/test_skeleton.py -v
```

**Coverage includes:**

- ✅ Skeleton structure validation
- ✅ Joint constraint validation
- ✅ Thickness map completeness
- ✅ Opt-in/opt-out validation behavior
- ✅ Bone hierarchy integrity

### Manual Verification

Visual verification script:

```bash
python tests/manual/verify_avatar.py
```

Expected output:

```
🧪 Verifying VoxelAvatar Structure...
✅ Created VoxelAvatar with root: VoxelAvatar
  ✅ Found visual node for: hips
  ✅ Found visual node for: spine
  ...
```

## Migration Guide

### Updating Existing Code

If you have code that creates `VoxelAvatar` instances:

**Before:**

```python
avatar = VoxelAvatar(parent_node, skeleton)
```

**After (no change needed):**

```python
# Validation now runs automatically
avatar = VoxelAvatar(parent_node, skeleton)
```

**If you need to disable validation:**

```python
avatar = VoxelAvatar(parent_node, skeleton, validate=False)
```

### Breaking Changes

✅ **None** - All changes are backward compatible. Validation is additive and can be opt-out.

## Reference

### Key Classes

- **`HumanoidSkeleton`** ([skeleton.py](file:///home/jamest/Desktop/dev/mycraft/engine/animation/skeleton.py))
  - `EXPECTED_BONE_NAMES`: Canonical bone list
  - `validate_structure()`: Validates skeleton integrity
  - `validate_constraints()`: Validates joint constraints
  - `get_expected_bones()`: Returns expected bone names

- **`VoxelAvatar`** ([voxel_avatar.py](file:///home/jamest/Desktop/dev/mycraft/engine/animation/voxel_avatar.py))
  - `BONE_THICKNESS_MAP`: Standard thickness values
  - `validate_avatar()`: Validates avatar integrity
  - `__init__(validate=True)`: Enable/disable validation

### Further Reading

- [Animation System Architecture](file:///home/jamest/Desktop/dev/mycraft/docs/ARCHITECTURE.md)
- [Testing Guide](file:///home/jamest/Desktop/dev/mycraft/docs/testing/testing_guide.md)
- [Player Mechanics Documentation](file:///home/jamest/Desktop/dev/mycraft/docs/player_mechanics.md)
