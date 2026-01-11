"""
Editor UI Theme

Centralized color palette, spacing, and text scales for consistent UI.
"""

from panda3d.core import Vec4


class Colors:
    """Standard color palette for editor UI."""
    
    # Backgrounds
    BG_PANEL = (0.12, 0.12, 0.14, 1)
    BG_DARK = (0.10, 0.10, 0.10, 0.95)
    BG_LIGHTER = (0.15, 0.15, 0.18, 1)
    
    # Accents
    ACCENT_PRIMARY = (0.3, 0.4, 0.6, 1)
    ACCENT_SUCCESS = (0.2, 0.6, 0.2, 1)
    ACCENT_WARNING = (0.8, 0.6, 0.2, 1)
    ACCENT_DANGER = (0.8, 0.3, 0.3, 1)
    
    # Text
    TEXT_PRIMARY = (0.9, 0.9, 0.9, 1)
    TEXT_SECONDARY = (0.7, 0.7, 0.7, 1)
    TEXT_MUTED = (0.5, 0.5, 0.5, 1)
    TEXT_HIGHLIGHT = (0.4, 0.8, 1.0, 1)
    
    # Buttons
    BTN_DEFAULT = (0.25, 0.25, 0.25, 1)
    BTN_HOVER = (0.30, 0.30, 0.35, 1)
    BTN_SELECTED = (0.40, 0.40, 0.60, 1)
    
    # Selection
    SELECTION = (0.4, 0.4, 0.6, 1)
    SELECTION_ACTIVE = (0.2, 0.6, 0.2, 1)


class Spacing:
    """Standard spacing values (in aspect2d units)."""
    
    PANEL_PADDING = 0.05
    ITEM_GAP = 0.08
    SECTION_GAP = 0.12
    BUTTON_HEIGHT = 0.06
    SLIDER_HEIGHT = 0.04


class TextScale:
    """Standard text scales."""
    
    HEADER = 0.045
    SUBHEADER = 0.04
    LABEL = 0.035
    BUTTON = 0.035
    SMALL = 0.03


class FrameSize:
    """Standard frame sizes for common UI elements."""
    
    # Sidebar panel (left/right)
    SIDEBAR = (-0.35, 0.35, -0.9, 0.9)
    
    # Compact panel (tools, layer control)
    COMPACT = (-0.2, 0.2, -0.12, 0.12)
    
    # Standard button hitbox (relative to text_scale=0.035)
    BUTTON = (-0.12, 0.12, -0.025, 0.035)
    
    # Small button (tool icons)
    BUTTON_SM = (-0.08, 0.08, -0.02, 0.028)
