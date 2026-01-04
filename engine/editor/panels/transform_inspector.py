from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectSlider
from panda3d.core import TextNode

class TransformInspectorPanel:
    """Right sidebar showing transform properties."""
    
    def __init__(self, parent, selection, callbacks):
        self.selection = selection
        self.callbacks = callbacks # Dict of callback functions
        
        # Main container
        self.frame = DirectFrame(
            parent=parent,
            frameColor=(0.12, 0.12, 0.14, 1),
            frameSize=(-0.35, 0.35, -0.9, 0.9),
            pos=(1.0, 0, 0)
        )
        
        # Header
        DirectLabel(
            parent=self.frame,
            text="Properties",
            scale=0.045,
            pos=(-0.3, 0, 0.85),
            text_fg=(0.9, 0.9, 0.9, 1),
            text_align=TextNode.ALeft,
            frameColor=(0,0,0,0)
        )
        
        self.sliders = {}
        self._build_controls()
        self.frame.hide() # Hidden until selection
        
    def _build_controls(self):
        y = 0.75
        
        # Selected Bone Label
        self.bone_label = DirectLabel(
            parent=self.frame,
            text="None",
            scale=0.04,
            pos=(0, 0, y),
            text_fg=(0.4, 0.8, 1.0, 1),
            frameColor=(0,0,0,0)
        )
        y -= 0.1
        
        # Helper to make section
        def make_section(title, sliders_def):
            nonlocal y
            DirectLabel(
                parent=self.frame,
                text=title,
                scale=0.035,
                pos=(-0.3, 0, y),
                text_fg=(0.7, 0.7, 0.7, 1),
                text_align=TextNode.ALeft,
                frameColor=(0,0,0,0)
            )
            y -= 0.08
            
            for axis, label, rng, step, cmd in sliders_def:
                DirectLabel(
                    parent=self.frame,
                    text=label,
                    scale=0.03,
                    pos=(-0.3, 0, y),
                    text_fg=(0.6, 0.6, 0.6, 1),
                    frameColor=(0,0,0,0)
                )
                
                s = DirectSlider(
                    parent=self.frame,
                    range=rng,
                    value=0,
                    pageSize=step,
                    scale=0.25,
                    pos=(0.0, 0, y),
                    command=cmd,
                    extraArgs=[axis]
                )
                self.sliders[f"{title}_{axis}"] = s
                y -= 0.08
            y -= 0.05

        # Position Section
        make_section("Position", [
            ('x', 'X', (-2, 2), 0.1, self.callbacks.get('pos')),
            ('y', 'Y', (-2, 2), 0.1, self.callbacks.get('pos')),
            ('z', 'Z', (-2, 2), 0.1, self.callbacks.get('pos'))
        ])
        
        # Rotation Section
        make_section("Rotation", [
            ('h', 'H', (-180, 180), 10, self.callbacks.get('rot')),
            ('p', 'P', (-180, 180), 10, self.callbacks.get('rot')),
            ('r', 'R', (-180, 180), 10, self.callbacks.get('rot'))
        ])
        
        # Length Section
        DirectLabel(
            parent=self.frame,
            text="Bone Length",
            scale=0.035,
            pos=(-0.3, 0, y),
            text_fg=(0.7, 0.7, 0.7, 1),
            text_align=TextNode.ALeft,
            frameColor=(0,0,0,0)
        )
        y -= 0.08
        self.length_slider = DirectSlider(
            parent=self.frame,
            range=(0.05, 1.0),
            value=0.3,
            pageSize=0.05,
            scale=0.25,
            pos=(0.0, 0, y),
            command=self.callbacks.get('length')
        )
        
    def update(self):
        """Update UI from selection."""
        if not self.selection or not self.selection.bone:
            self.frame.hide()
            return
            
        self.frame.show()
        self.bone_label['text'] = self.selection.bone
        
        # Note: True bidirectional binding would require reading from avatar
        # For drag, we might not update sliders every frame to avoid perf hit
        # But for clicks we should.
        # Requires access to avatar/skeleton in update()
        
    def cleanup(self):
        self.frame.destroy()
