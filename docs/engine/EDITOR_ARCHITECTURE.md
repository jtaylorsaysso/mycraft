# Editor Architecture

**For Tool Developers**

The MyCraft Editor Suite is a standalone application that runs separately from the main game. This architecture allows for lightweight, fast tooling without the overhead of the full ECS game loop or world generation.

---

## Overview

The system consists of three core components:

1. **EditorApp**: A lightweight `ShowBase` subclass that provides the Panda3D runtime foundation.
2. **EditorSuiteManager**: A tab-based navigation system for switching between different tools (Model Editor, Animation Editor).
3. **EditorSelection**: A shared state container that allows tools to communicate (e.g., selecting a bone in one tool and seeing it highlighted in another).

### Directory Structure

```text
engine/editor/
├── app.py              # The main application entry point
├── manager.py          # Tab/sidebar navigation manager
├── selection.py        # Shared selection state
└── tools/
    ├── model_editor.py        # Voxel character editor
    ├── animation_editor.py    # Animation timing editor
    └── common/                # Shared widgets (gizmos, timelines)
```

---

## Core Components

### 1. EditorApp

Located in `engine.editor.app`, this class initializes the Panda3D window and shared resources.

**Key responsibilities**:

- Window setup (title, dimensions)
- Asset Manager initialization
- Global shortcut handling (ESC to quit)
- Hosting the `EditorSuiteManager`

**Shared Resources**:

```python
self.anim_registry = get_animation_registry()
self.asset_manager = AssetManager("assets")
```

### 2. EditorSuiteManager

Located in `engine.editor.manager`, this handles the side-bar navigation.

**Key features**:

- **Lazy Loading**: Tools are imported only when requested to prevent circular dependencies.
- **Cleanup**: Calls `cleanup()` on tools when switching or exiting.
- **Keyboard Shortcuts**: `1-9` keys switch between active tools.

**Registering a new tool**:

```python
# In EditorApp._setup_editors()
from engine.editor.tools.my_new_tool import MyNewTool
tool_instance = MyNewTool(self)
self.suite_manager.add_editor("My Tool", tool_instance)
```

### 3. EditorSelection

Located in `engine.editor.selection`, this observer-based class manages state shared between tools.

**Usage**:

```python
# In a tool
self.selection.bone = "hand_right"

# In another tool
self.selection.add_observer(self._on_selection_changed)

def _on_selection_changed(self, prop, value):
    if prop == "bone":
        print(f"Selected bone: {value}")
```

---

## Creating a New Tool

To create a new editor tool, implement a class with the following interface:

```python
class MyTool:
    def __init__(self, app):
        self.app = app
        self.root = getattr(app, 'render', None)
        
    def set_selection(self, selection):
        """Receive shared selection object."""
        self.selection = selection
        
    def show(self):
        """Called when tool becomes active."""
        # Create UI, show 3D objects
        
    def hide(self):
        """Called when switching away."""
        # Hide UI, hide 3D objects
        
    def cleanup(self):
        """Called on application exit."""
        # Destroy resources
```

---

## Common Utilities

The `engine.editor.tools.common` package provides reusable components:

- **TransformGizmo**: 3D manipulator for Move/Rotate/Scale.
- **BonePicker**: Raycasting helper for selecting 3D bones.
- **TimelineWidget**: Visual timeline for animation data.
- **SplineGizmo**: Control points for curve editing.

---

*Last Updated: 2026-01-03*
