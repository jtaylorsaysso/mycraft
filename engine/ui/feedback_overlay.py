from direct.gui.DirectGui import *
from panda3d.core import TextNode, Vec4

class FeedbackOverlay:
    def __init__(self, on_submit_callback, on_cancel_callback):
        self.on_submit = on_submit_callback
        self.on_cancel = on_cancel_callback
        
        # Colors (Dark Theme)
        self.bg_color = (0.1, 0.1, 0.1, 0.95)
        self.input_bg = (0.2, 0.2, 0.2, 1)
        self.text_color = (0.9, 0.9, 0.9, 1)
        self.btn_color = (0.2, 0.6, 1.0, 1)
        self.cancel_color = (0.6, 0.2, 0.2, 1)
        
        # Create semi-transparent background frame
        self.frame = DirectFrame(
            frameColor=self.bg_color,
            frameSize=(-1.2, 1.2, -0.9, 0.9),  # Centered, covering most screen
            pos=(0, 0, 0),
            parent=aspect2d,
            relief=DGG.FLAT
        )
        
        # Title
        self.title_label = DirectLabel(
            text="Report Bug or Feedback",
            scale=0.08,
            pos=(0, 0, 0.75),
            text_fg=self.text_color,
            frameColor=(0, 0, 0, 0),
            parent=self.frame
        )
        
        # --- Form Fields ---
        
        # Label: Title
        DirectLabel(
            text="Title:",
            scale=0.05,
            pos=(-1.0, 0, 0.6),
            text_align=TextNode.ALeft,
            text_fg=self.text_color,
            frameColor=(0,0,0,0),
            parent=self.frame
        )
        
        # Input: Title
        self.title_entry = DirectEntry(
            scale=0.05,
            pos=(-1.0, 0, 0.5),
            width=40,  # Scaled width
            numLines=1,
            frameColor=self.input_bg,
            text_fg=self.text_color,
            initialText="",
            focus=0,
            parent=self.frame
        )
        
        # Label: Category
        DirectLabel(
            text="Category:",
            scale=0.05,
            pos=(0.2, 0, 0.6),
            text_align=TextNode.ALeft,
            text_fg=self.text_color,
            frameColor=(0,0,0,0),
            parent=self.frame
        )
        
        # Dropdown: Category
        # Note: DirectOptionMenu items is a list of strings
        self.category_menu = DirectOptionMenu(
            text="Bug",
            scale=0.05,
            items=["Bug", "Suggestion", "Question", "Other"],
            initialitem=0,
            pos=(0.2, 0, 0.5),
            highlightColor=(0.3, 0.3, 0.3, 1),
            frameColor=self.input_bg,
            text_fg=self.text_color,
            parent=self.frame
        )
        
        # Label: Description
        DirectLabel(
            text="Description:",
            scale=0.05,
            pos=(-1.0, 0, 0.35),
            text_align=TextNode.ALeft,
            text_fg=self.text_color,
            frameColor=(0,0,0,0),
            parent=self.frame
        )
        
        # Input: Description (Multi-line simulation via DirectEntry often single line, 
        # but huge width helps. True multi-line is tricky in basic DirectGUI without scrolling)
        # We'll stick to a large input field.
        self.description_entry = DirectEntry(
            scale=0.045,
            pos=(-1.0, 0, 0.25),
            width=45,
            numLines=5,
            frameColor=self.input_bg,
            text_fg=self.text_color,
            initialText="",
            focus=0,
            parent=self.frame
        )
        
        # Label: Attachments
        DirectLabel(
            text="Attachments:",
            scale=0.05,
            pos=(-1.0, 0, -0.1),
            text_align=TextNode.ALeft,
            text_fg=self.text_color,
            frameColor=(0,0,0,0),
            parent=self.frame
        )
        
        # Checkbox: Screenshot
        self.screenshot_checkbox = DirectCheckButton(
            text="Include Screenshot",
            scale=0.05,
            pos=(-0.9, 0, -0.2),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            indicatorValue=1,
            boxBorder=0,
            boxRelief=DGG.FLAT,
            parent=self.frame
        )
        
        # Checkbox: Logs
        self.logs_checkbox = DirectCheckButton(
            text="Include Logs (Last 500 lines)",
            scale=0.05,
            pos=(-0.2, 0, -0.2),
            text_fg=self.text_color,
            text_align=TextNode.ALeft,
            indicatorValue=1,
            boxBorder=0,
            boxRelief=DGG.FLAT,
            parent=self.frame
        )
        
        # --- Buttons ---
        
        # Submit
        self.submit_button = DirectButton(
            text="Submit Report",
            scale=0.06,
            pos=(0.3, 0, -0.6),
            frameColor=self.btn_color,
            text_fg=(1,1,1,1),
            command=self._on_submit_clicked,
            parent=self.frame,
            relief=DGG.RAISED
        )
        
        # Cancel
        self.cancel_button = DirectButton(
            text="Cancel",
            scale=0.06,
            pos=(-0.3, 0, -0.6),
            frameColor=self.cancel_color,
            text_fg=(1,1,1,1),
            command=self.on_cancel,
            parent=self.frame,
            relief=DGG.RAISED
        )
        
        # Privacy Notice
        privacy_text = (
            "Privacy Notice:\n"
            "Reports are saved LOCALLY to 'reports/' folder.\n"
            "We collect: System info, Game logs, Session stats.\n"
            "No personal files are accessed."
        )
        DirectLabel(
            text=privacy_text,
            scale=0.035,
            pos=(0, 0, -0.8),
            text_fg=(0.7, 0.7, 0.7, 1),
            frameColor=(0,0,0,0),
            parent=self.frame
        )
        
        # Start hidden
        self.hide()
    
    def show(self):
        self.frame.show()
        # Reset fields if preferred, or keep them. 
        # Typically nice to keep them if user cancelled by accident, 
        # but we'll clear 'em for a fresh report or not? 
        # Let's keep state for now.
        
    def hide(self):
        self.frame.hide()
        
    def _on_submit_clicked(self):
        title = self.title_entry.get().strip()
        description = self.description_entry.get().strip()
        
        if not title:
            # Simple validation feedback (shake or visual?)
            # For now just force focus back or print
            self.title_entry['frameColor'] = (0.5, 0.1, 0.1, 1)
            return
            
        self.title_entry['frameColor'] = self.input_bg
        
        data = {
            "title": title,
            "description": description,
            "category": self.category_menu.get(),
            "include_screenshot": bool(self.screenshot_checkbox['indicatorValue']),
            "include_logs": bool(self.logs_checkbox['indicatorValue'])
        }
        self.on_submit(data)
        
        # Clear fields after successful submit
        self.title_entry.enterText("")
        self.description_entry.enterText("")
