from direct.gui.DirectGui import *
from panda3d.core import TextNode, Vec4
import json
from pathlib import Path

class SettingsOverlay:
    def __init__(self, base, hot_config):
        self.base = base
        self.config = hot_config
        self.visible = False
        
        # Colors (Dark Theme)
        self.bg_color = (0.1, 0.1, 0.1, 0.95)
        self.panel_color = (0.15, 0.15, 0.15, 1)
        self.text_color = (0.9, 0.9, 0.9, 1)
        self.btn_color = (0.2, 0.6, 1.0, 1)
        self.accent_color = (0.2, 0.8, 0.2, 1)
        
        # Main Frame
        self.frame = DirectFrame(
            frameColor=self.bg_color,
            frameSize=(-0.8, 0.8, -0.7, 0.7),
            pos=(0, 0, 0),
            parent=base.aspect2d,
            relief=DGG.FLAT
        )
        self.frame.hide()
        
        # Title
        DirectLabel(
            text="SETTINGS",
            scale=0.08,
            pos=(0, 0, 0.55),
            text_fg=self.text_color,
            frameColor=(0,0,0,0),
            parent=self.frame
        )
        
        # State tracking for sliders
        self.controls = {}
        
        # Build UI
        self._build_content()
        self._build_footer()
        
    def _build_content(self):
        # We'll use a simple vertical layout for now, categorized by headers
        start_y = 0.4
        spacing = 0.12
        
        # --- Movement ---
        self._add_header("MOVEMENT", -0.6, start_y)
        self.controls['movement_speed'] = self._add_slider("Speed", -0.6, start_y - spacing, 1.0, 20.0, "movement_speed")
        self.controls['jump_height'] = self._add_slider("Jump", -0.6, start_y - spacing*2, 1.0, 10.0, "jump_height")
        self.controls['gravity'] = self._add_slider("Gravity", -0.6, start_y - spacing*3, -30.0, -5.0, "gravity")
        
        # --- Camera ---
        self._add_header("CAMERA", 0.2, start_y)
        self.controls['mouse_sensitivity'] = self._add_slider("Sens.", 0.2, start_y - spacing, 10.0, 100.0, "mouse_sensitivity")
        self.controls['fov'] = self._add_slider("FOV", 0.2, start_y - spacing*2, 60.0, 120.0, "fov", int_val=True)
        self.controls['camera_distance'] = self._add_slider("Dist.", 0.2, start_y - spacing*3, 2.0, 10.0, "camera_distance")
        
        # --- Toggles ---
        toggle_y = -0.1
        self.controls['god_mode'] = self._add_toggle("God Mode", -0.5, toggle_y, "god_mode")
        self.controls['debug_overlay'] = self._add_toggle("Debug Info", 0.3, toggle_y, "debug_overlay")

    def _add_header(self, text, x, y):
        DirectLabel(
            text=text,
            scale=0.05,
            pos=(x, 0, y),
            text_fg=self.accent_color,
            text_align=TextNode.ALeft,
            frameColor=(0,0,0,0),
            parent=self.frame
        )

    def _add_slider(self, label, x, y, min_val, max_val, config_key, int_val=False):
        # Label
        DirectLabel(
            text=label,
            scale=0.04,
            pos=(x, 0, y + 0.01),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            frameColor=(0,0,0,0),
            parent=self.frame
        )
        
        # Current Value from config
        current_val = self.config.get(config_key)
        # Handle defaults if missing
        if current_val is None:
            current_val = (min_val + max_val) / 2
            
        # Slider
        slider = DirectSlider(
            range=(min_val, max_val),
            value=current_val,
            pageSize=(max_val-min_val)/10,
            scale=0.25,
            pos=(x + 0.35, 0, y + 0.02),
            command=lambda: self._on_slider_change(config_key, slider, int_val),
            parent=self.frame
        )
        
        # Value Label
        val_label = DirectLabel(
            text=f"{current_val:.1f}",
            scale=0.04,
            pos=(x + 0.65, 0, y + 0.01),
            text_fg=self.text_color,
            text_align=TextNode.ARight,
            frameColor=(0,0,0,0),
            parent=self.frame
        )
        
        # Store ref to label on slider for easy update
        slider.val_label = val_label
        return slider

    def _add_toggle(self, label, x, y, config_key):
        val = bool(self.config.get(config_key))
        
        chk = DirectCheckButton(
            text=label,
            scale=0.05,
            pos=(x, 0, y),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            indicatorValue=1 if val else 0,
            boxBorder=0,
            boxRelief=DGG.FLAT,
            command=lambda v: self._on_toggle_change(config_key, v),
            parent=self.frame
        )
        return chk

    def _build_footer(self):
        # Save Button
        DirectButton(
            text="SAVE",
            scale=0.06,
            pos=(0.3, 0, -0.5),
            frameColor=self.btn_color,
            text_fg=(1,1,1,1),
            command=self.save_settings,
            parent=self.frame,
            relief=DGG.RAISED
        )
        
        # Reset Button
        DirectButton(
            text="RESET",
            scale=0.06,
            pos=(-0.3, 0, -0.5),
            frameColor=(0.5, 0.5, 0.5, 1),
            text_fg=(1,1,1,1),
            command=self.reset_settings,
            parent=self.frame,
            relief=DGG.RAISED
        )
        
        # Close Hint
        DirectLabel(
            text="Press ESC to Close",
            scale=0.04,
            pos=(0, 0, -0.62),
            text_fg=(0.6, 0.6, 0.6, 1),
            frameColor=(0,0,0,0),
            parent=self.frame
        )

    def _on_slider_change(self, key, slider, int_val):
        val = slider['value']
        if int_val:
            val = int(val)
            slider.val_label['text'] = f"{val}"
        else:
            slider.val_label['text'] = f"{val:.1f}"
            
        # Live update
        self.config.set(key, val)

    def _on_toggle_change(self, key, val):
        self.config.set(key, bool(val))

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()
            
    def show(self):
        self.visible = True
        self.frame.show()
        self._refresh_ui_from_config()
        
    def hide(self):
        self.visible = False
        self.frame.hide()

    def _refresh_ui_from_config(self):
        """Update UI elements to match current config values (in case changed externally)."""
        # This is a bit tricky with DirectGui without rebuilding, but we can set values
        # For prototype simplicity, we rely on the fact that opening the menu is the primary sync point
        pass

    def save_settings(self):
        self.config.save()
        # Visual feedback?
        
    def reset_settings(self):
        # Reload from disk? Or defaults? For now, reload disk
        # Ideally we'd have a 'defaults' dict to revert to.
        # Let's just reload the file to revert unsaved changes
        # But wait, self.config.set() updates memory immediately.
        # So 'Reset' implies reverting to what was on disk, OR reverting to factory defaults.
        # Let's assume revert to disk.
        pass
