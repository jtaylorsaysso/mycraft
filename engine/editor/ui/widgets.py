"""
Standard editor UI widgets.

Provides consistent buttons, labels, sliders, and other controls.
"""

from typing import Callable, Optional, Any, List
from direct.gui.DirectGui import (
    DirectButton, DirectLabel, DirectSlider, DirectFrame,
    DirectOptionMenu, DirectCheckButton, DGG
)
from panda3d.core import TextNode

from engine.editor.ui.theme import Colors, Spacing, TextScale, FrameSize


def EditorButton(
    parent,
    text: str,
    command: Optional[Callable] = None,
    extraArgs: Optional[List] = None,
    pos=(0, 0, 0),
    color: str = "default",
    size: str = "normal"
) -> DirectButton:
    """
    Create a standard editor button.
    
    Args:
        parent: Parent GUI node
        text: Button label
        command: Click callback
        extraArgs: Extra arguments for command
        pos: Position tuple
        color: "default", "primary", "success", "warning", "danger"
        size: "normal" or "small"
        
    Returns:
        DirectButton instance
    """
    color_map = {
        "default": Colors.BTN_DEFAULT,
        "primary": Colors.ACCENT_PRIMARY,
        "success": Colors.ACCENT_SUCCESS,
        "warning": Colors.ACCENT_WARNING,
        "danger": Colors.ACCENT_DANGER,
    }
    
    frame_size = FrameSize.BUTTON if size == "normal" else FrameSize.BUTTON_SM
    text_scale = TextScale.BUTTON if size == "normal" else TextScale.SMALL
    
    return DirectButton(
        parent=parent,
        text=text,
        text_scale=text_scale,
        text_fg=Colors.TEXT_PRIMARY,
        pos=pos,
        frameColor=color_map.get(color, Colors.BTN_DEFAULT),
        frameSize=frame_size,
        command=command,
        extraArgs=extraArgs or [],
        relief=DGG.FLAT
    )


def EditorLabel(
    parent,
    text: str,
    pos=(0, 0, 0),
    scale: str = "label",
    color: str = "primary",
    align: str = "left"
) -> DirectLabel:
    """
    Create a standard editor label.
    
    Args:
        parent: Parent GUI node
        text: Label text
        pos: Position tuple
        scale: "header", "subheader", "label", "small"
        color: "primary", "secondary", "muted", "highlight"
        align: "left", "center", "right"
        
    Returns:
        DirectLabel instance
    """
    scale_map = {
        "header": TextScale.HEADER,
        "subheader": TextScale.SUBHEADER,
        "label": TextScale.LABEL,
        "small": TextScale.SMALL,
    }
    
    color_map = {
        "primary": Colors.TEXT_PRIMARY,
        "secondary": Colors.TEXT_SECONDARY,
        "muted": Colors.TEXT_MUTED,
        "highlight": Colors.TEXT_HIGHLIGHT,
    }
    
    align_map = {
        "left": TextNode.ALeft,
        "center": TextNode.ACenter,
        "right": TextNode.ARight,
    }
    
    return DirectLabel(
        parent=parent,
        text=text,
        scale=scale_map.get(scale, TextScale.LABEL),
        pos=pos,
        text_fg=color_map.get(color, Colors.TEXT_PRIMARY),
        text_align=align_map.get(align, TextNode.ALeft),
        frameColor=(0, 0, 0, 0)
    )


def EditorSlider(
    parent,
    pos=(0, 0, 0),
    range: tuple = (0, 1),
    value: float = 0,
    command: Optional[Callable] = None,
    extraArgs: Optional[List] = None,
    width: float = 0.25
) -> DirectSlider:
    """
    Create a standard editor slider.
    
    Args:
        parent: Parent GUI node
        pos: Position tuple
        range: (min, max) tuple
        value: Initial value
        command: Change callback
        extraArgs: Extra arguments for command
        width: Slider width (scale)
        
    Returns:
        DirectSlider instance
    """
    return DirectSlider(
        parent=parent,
        pos=pos,
        range=range,
        value=value,
        scale=width,
        command=command,
        extraArgs=extraArgs or []
    )


def SectionHeader(parent, text: str, pos=(0, 0, 0)) -> DirectFrame:
    """
    Create a section header with separator line.
    
    Args:
        parent: Parent GUI node
        text: Section title
        pos: Position tuple
        
    Returns:
        DirectFrame containing label and separator
    """
    container = DirectFrame(
        parent=parent,
        frameColor=(0, 0, 0, 0),
        pos=pos
    )
    
    DirectLabel(
        parent=container,
        text=text,
        scale=TextScale.LABEL,
        pos=(0, 0, 0),
        text_fg=Colors.TEXT_SECONDARY,
        text_align=TextNode.ALeft,
        frameColor=(0, 0, 0, 0)
    )
    
    return container


def EditorDropdown(
    parent,
    items: List[str],
    pos=(0, 0, 0),
    command: Optional[Callable] = None,
    initial: int = 0
) -> DirectOptionMenu:
    """
    Create a standard dropdown menu.
    
    Args:
        parent: Parent GUI node
        items: List of option strings
        pos: Position tuple
        command: Selection callback
        initial: Initial selected index
        
    Returns:
        DirectOptionMenu instance
    """
    return DirectOptionMenu(
        parent=parent,
        items=items if items else ["(empty)"],
        scale=TextScale.LABEL,
        pos=pos,
        highlightColor=Colors.BTN_HOVER,
        command=command,
        initialitem=initial
    )
