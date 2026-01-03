# Editor UI Standards

> [!IMPORTANT]
> The Editor Suite follows a strict **Dark Mode** aesthetic with **Neon Accents** to provide a professional, modern game development environment.

## Visual Identity

### Color Palette

| Name | Hex | Usage |
| :--- | :--- | :--- |
| **Background Dark** | `#141414` | Global window background, canvas backdrop. |
| **Panel Surface** | `#1F1F1F` | Sidebars, floating panels, widgets. |
| **Panel Border** | `#333333` | 1px borders around panels. |
| **Accent Primary** | `#32CD32` | **Neon Green**. Selection highlights, primary buttons, active toggles. |
| **Accent Secondary** | `#2096F3` | **Sky Blue**. Secondary actions, information, sliders. |
| **Text Primary** | `#EEEEEE` | Main labels, input values. |
| **Text Muted** | `#888888` | Labels, hints, placeholder text. |
| **Error** | `#FF4444` | Validation errors, delete actions. |

### Typography

- **Font Family**: standard sans-serif (e.g., Roboto/Inter style available in Panda3D).
- **Scale**:
  - **Header**: 18px (Bold) - Panel Titles
  - **Body**: 14px (Regular) - Standard labels
  - **Small**: 12px (Regular) - Hints, status bars

---

## Layout Patterns

### Standard 3-Column Layout

Most editors should follow this layout:

1. **Left Sidebar (Tools/Hierarchy)**
    - Fixed width (e.g., 300px / 0.3 screen units).
    - Contains: Brushes, Asset/Scene Tree, Palettes.
2. **Center Viewport (Canvas)**
    - Flexible width.
    - Contains: The 3D scene, gizmos, grid.
3. **Right Sidebar (Inspector)**
    - Fixed width (e.g., 300px / 0.3 screen units).
    - Contains: Properties, Layers, Settings.

### Floating Overlays

- **Modal Dialogs**: Centered, semi-transparent black overlay.
- **Toasts/Notifications**: Bottom-right corner, auto-dismiss.

---

## Widget Guidelines

### Buttons

- **Primary**: Solid Accent Color (`#32CD32`), Black text.
- **Secondary**: Dark Grey (`#333333`), White text.
- **Icon-Only**: Transparent background, White icon (light up accent on hover).

### Sliders

- Background track: Dark Grey (`#111`).
- Fill track: Accent Color (`#2096F3` or `#32CD32`).
- Handle: White circle.

### Inputs

- Background: Very Dark (`#0A0A0A`).
- Border: `1px solid #333`. (Focus: Accent color border).

---

*Last Updated: 2026-01-01*
