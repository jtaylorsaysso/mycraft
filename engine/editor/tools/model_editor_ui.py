"""
ModelEditorUI: UI component for ModelEditor.
"""

from typing import Dict, Callable, Optional
from direct.gui.DirectGui import (
    DirectFrame, DirectButton, DirectLabel, DGG, DirectEntry
)
from panda3d.core import TextNode

from engine.editor.tools.common.drag_controller import DragMode

# Constants (duplicated/shared)
COLOR_PANEL_BG = (0.12, 0.12, 0.14, 0.95)
COLOR_HEADER_BG = (0.18, 0.18, 0.20, 1.0)
COLOR_BUTTON = (0.22, 0.22, 0.26, 1)
COLOR_BUTTON_ACTIVE = (0.3, 0.5, 0.3, 1)
COLOR_HINT_BG = (0.1, 0.1, 0.1, 0.8)

BONE_DISPLAY_NAMES = {
    "hips": "Hips", "spine": "Spine", "chest": "Chest", "head": "Head",
    "shoulder_left": "L Shoulder", "shoulder_right": "R Shoulder",
    "upper_arm_left": "L Upper Arm", "upper_arm_right": "R Upper Arm",
    "forearm_left": "L Forearm", "forearm_right": "R Forearm",
    "hand_left": "L Hand", "hand_right": "R Hand",
    "thigh_left": "L Thigh", "thigh_right": "R Thigh",
    "shin_left": "L Shin", "shin_right": "R Shin",
    "foot_left": "L Foot", "foot_right": "R Foot",
}


class ModelEditorUI:
    """Manages the main UI layout for the ModelEditor."""
    
    def __init__(self, parent_node, editor):
        """Initialize UI.
        
        Args:
            parent_node: Parent node for UI elements
            editor: ModelEditor instance (controller)
        """
        self.parent_node = parent_node
        self.editor = editor
        
        # UI Elements
        self.main_frame: Optional[DirectFrame] = None
        self.hint_label: Optional[DirectLabel] = None
        self.mode_buttons = {}
        self.symmetry_button: Optional[DirectButton] = None
        
        # Build layout
        self._build_main_frame()
        self._build_toolbar()
        self._build_bone_panel()
        self._build_hint_bar()
        
    def _build_main_frame(self):
        self.main_frame = DirectFrame(
            parent=self.parent_node,
            frameColor=(0, 0, 0, 0),
            frameSize=(-1.0, 1.4, -1.0, 1.0),
            pos=(0.0, 0, 0)
        )
        
    def _build_toolbar(self):
        """Build top toolbar with mode buttons."""
        toolbar = DirectFrame(
            parent=self.main_frame,
            frameColor=COLOR_HEADER_BG,
            frameSize=(-0.65, 0.95, 0.85, 0.98),
            pos=(0, 0, 0)
        )
        
        DirectLabel(
            parent=toolbar,
            text="Model Editor",
            scale=0.04,
            pos=(0.15, 0, 0.90),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        # Mode buttons
        modes = [
            ("Move", DragMode.MOVE, "G"),
            ("Rotate", DragMode.ROTATE, "R"),
            ("Scale", DragMode.SCALE, "S"),
        ]
        
        x_pos = 0.50
        for label, mode, hotkey in modes:
            btn = DirectButton(
                parent=toolbar,
                text=f"{label} [{hotkey}]",
                scale=0.028,
                pos=(x_pos, 0, 0.90),
                frameColor=COLOR_BUTTON, # Default color, updated later
                text_fg=(1, 1, 1, 1),
                command=self.editor._set_mode, # Call editor method
                extraArgs=[mode]
            )
            self.mode_buttons[mode] = btn
            x_pos += 0.15
            
        # Undo/Redo
        DirectButton(
            parent=toolbar,
            text="Undo",
            scale=0.025,
            pos=(-0.55, 0, 0.90),
            frameColor=COLOR_BUTTON,
            text_fg=(1, 1, 1, 1),
            command=self.editor._on_undo
        )
        DirectButton(
            parent=toolbar,
            text="Redo",
            scale=0.025,
            pos=(-0.42, 0, 0.90),
            frameColor=COLOR_BUTTON,
            text_fg=(1, 1, 1, 1),
            command=self.editor._on_redo
        )
        
        # Symmetry toggle
        self.symmetry_button = DirectButton(
            parent=toolbar,
            text="✓ Symmetry",
            scale=0.028,
            pos=(-0.25, 0, 0.90),
            frameColor=COLOR_BUTTON,
            text_fg=(1, 1, 1, 1),
            command=self.editor._toggle_symmetry
        )
        
        # Spine Mode toggle
        self.spine_button = DirectButton(
            parent=toolbar,
            text="Spine Mode",
            scale=0.028,
            pos=(-0.08, 0, 0.90),
            frameColor=COLOR_BUTTON,
            text_fg=(1, 1, 1, 1),
            command=self.editor._toggle_spine_mode
        )
        
        # Save/Load
        DirectButton(
            parent=toolbar,
            text="Save",
            scale=0.028,
            pos=(0.10, 0, 0.90),
            frameColor=COLOR_BUTTON,
            text_fg=(1, 1, 1, 1),
            command=self.editor._on_save_request
        )
        DirectButton(
            parent=toolbar,
            text="Load",
            scale=0.028,
            pos=(0.20, 0, 0.90),
            frameColor=COLOR_BUTTON,
            text_fg=(1, 1, 1, 1),
            command=self.editor._on_load_request
        )

    def _build_bone_panel(self):
        """Build left panel with bone list."""
        panel = DirectFrame(
            parent=self.main_frame,
            frameColor=COLOR_PANEL_BG,
            frameSize=(-0.35, 0.35, -0.8, 0.8),
            pos=(-0.95, 0, 0)
        )
        
        DirectLabel(
            parent=panel,
            text="Hierarchy",
            scale=0.045,
            pos=(0, 0, 0.72),
            text_fg=(1, 1, 1, 1),
            frameColor=(0, 0, 0, 0)
        )
        
        # Scrollable list of bones (simplified as buttons for now)
        # Using a canvas for scrolling would be better but keeping simple for now
        # Just listing key bones
        
        y_pos = 0.65
        indent_map = {
            "hips": 0, "spine": 1, "chest": 2, "head": 3,
            "shoulder": 2, "upper_arm": 3, "forearm": 4, "hand": 5,
            "thigh": 1, "shin": 2, "foot": 3
        }
        
        # Order implies hierarchy roughly for display
        display_order = [
            "hips", "spine", "chest", "head",
            "shoulder_left", "upper_arm_left", "forearm_left", "hand_left",
            "shoulder_right", "upper_arm_right", "forearm_right", "hand_right",
            "thigh_left", "shin_left", "foot_left",
            "thigh_right", "shin_right", "foot_right"
        ]
        
        for bone_name in display_order:
            if bone_name not in self.editor.avatar.bone_nodes:
                continue
                
            display_name = BONE_DISPLAY_NAMES.get(bone_name, bone_name.capitalize())
            
            # Determine indentation
            base_name = bone_name.split("_")[0]
            indent = indent_map.get(base_name, 0) * 0.03
            
            DirectButton(
                parent=panel,
                text=display_name,
                scale=0.035,
                text_align=TextNode.ALeft,
                pos=(-0.25 + indent, 0, y_pos),
                frameColor=(0, 0, 0, 0),
                text_fg=(0.8, 0.8, 0.8, 1),
                command=self.editor._select_bone,
                extraArgs=[bone_name],
                relief=DGG.FLAT
            )
            y_pos -= 0.06

    def _build_hint_bar(self):
        """Build contextual hint bar at bottom."""
        self.hint_label = DirectLabel(
            parent=self.main_frame,
            text="Initializing...",
            scale=0.04,
            frameColor=COLOR_HINT_BG,
            frameSize=(-0.8, 0.8, -0.05, 0.05),
            text_fg=(1, 1, 1, 1),
            pos=(0, 0, -0.90)
        )

    # Public Update Methods
    
    def set_active_mode(self, mode: DragMode):
        """Update active mode button style."""
        for m, btn in self.mode_buttons.items():
            btn['frameColor'] = COLOR_BUTTON_ACTIVE if m == mode else COLOR_BUTTON
            
    def set_symmetry_active(self, enabled: bool):
        """Update symmetry button style."""
        if self.symmetry_button:
            self.symmetry_button['text'] = "✓ Symmetry" if enabled else "Symmetry"
            self.symmetry_button['frameColor'] = COLOR_BUTTON_ACTIVE if enabled else COLOR_BUTTON
            
    def set_hint(self, text: str):
        """Set hint text."""
        if self.hint_label:
            self.hint_label['text'] = text
        
    def show(self):
        self.main_frame.show()
        
    def hide(self):
        self.main_frame.hide()
        
    def show_io_dialog(self, title: str, on_confirm: Callable[[str], None], on_cancel: Callable[[], None]):
        """Show a simple modal dialog for filename input.
        
        Args:
            title: Title text (e.g. "Save Avatar")
            on_confirm: Callback with entered text
            on_cancel: Callback on cancel
        """
        # Dim background
        bg = DirectFrame(
            parent=self.main_frame,
            frameColor=(0, 0, 0, 0.5),
            frameSize=(-2, 2, -2, 2),
            pos=(0, 0, 0),
            state=DGG.NORMAL # Block clicks
        )
        
        frame = DirectFrame(
            parent=bg,
            frameColor=COLOR_HEADER_BG,
            frameSize=(-0.5, 0.5, -0.3, 0.3),
            pos=(0, 0, 0)
        )
        
        DirectLabel(
            parent=frame,
            text=title,
            scale=0.05,
            pos=(0, 0, 0.15),
            text_fg=(1, 1, 1, 1),
            frameColor=(0,0,0,0)
        )
        
        entry = DirectEntry(
            parent=frame,
            scale=0.04,
            width=20,
            pos=(-0.4, 0, 0.0),
            text_fg=(0,0,0,1),
            initialText="hero_model",
            focus=1
        )
        
        def _cleanup():
            bg.destroy()
            
        def _on_ok():
            text = entry.get()
            _cleanup()
            on_confirm(text)
            
        def _on_cancel():
            _cleanup()
            on_cancel()
            
        DirectButton(
            parent=frame,
            text="Confirm",
            scale=0.04,
            pos=(0.2, 0, -0.15),
            command=_on_ok
        )
        DirectButton(
            parent=frame,
            text="Cancel",
            scale=0.04,
            pos=(-0.2, 0, -0.15),
            command=_on_cancel
        )
        
    def cleanup(self):
        if self.main_frame:
            self.main_frame.removeNode()
