# Equipment Sockets

**For Gameplay Programmers**

The Socket system defines attachment points on the character skeleton where equipment (weapons, tools, armor) can be parented. It acts as an abstraction layer so items don't need to know about specific bone names or offsets.

---

## Overview

A `Socket` is a named attachment point relative to a specific bone, with position and rotation offsets.

**Core Class**: `engine.animation.skeleton.Socket`

```python
@dataclass
class Socket:
    name: str              # Unique identifier (e.g., "hand_r_socket")
    parent_bone_name: str  # Bone to attach to (e.g., "hand_right")
    offset_position: LVector3f
    offset_rotation: LVector3f
```

---

## Standard Sockets

The `HumanoidSkeleton` comes pre-configured with the following sockets:

| Socket Name | Parent Bone | Position | Use Case |
|:--|:--|:--|:--|
| `hand_r_socket` | `hand_right` | Center of palm | Main hand weapons (swords, picks) |
| `hand_l_socket` | `hand_left` | Center of palm | Off-hand items (shields, torches) |
| `back_socket` | `chest` | Upper back | Sheathed large weapons (greatswords) |
| `belt_r_socket` | `hips` | Right hip | Sheathed small items (daggers) |
| `belt_l_socket` | `hips` | Left hip | Sheathed small items (potions) |

---

## API Usage

### Getting a Socket's Transform

To attach an item, you need the socket's world transform, which combines the parent bone's world transform with the socket's local offsets.

```python
def attach_item_to_socket(item_node: NodePath, skeleton: Skeleton, socket_name: str):
    socket = skeleton.get_socket(socket_name)
    if not socket:
        return
        
    parent_bone = skeleton.get_bone(socket.parent_bone_name)
    if not parent_bone:
        return
        
    # 1. Get Parent Bone World Transform
    bone_transform = parent_bone.world_transform
    
    # 2. Attach item to the Bone's NodePath (if available)
    # This lets Panda3D handle the hierarchy automatically
    if bone_node_path:
        item_node.reparentTo(bone_node_path)
        item_node.setPos(socket.offset_position)
        item_node.setHpr(socket.offset_rotation)
```

### Adding Custom Sockets

You can add dynamic sockets at runtime (e.g., "arrow_stuck_in_knee"):

```python
skeleton.add_socket(
    name="knee_hit_point",
    parent_bone_name="shin_left",
    offset_position=LVector3f(0, 0.2, 0)
)
```

---

*Last Updated: 2026-01-03*
