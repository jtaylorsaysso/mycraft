import sys
import platform
import zipfile
import json
import uuid
from datetime import datetime
from pathlib import Path
from engine.ecs.system import System
from engine.ui.feedback_overlay import FeedbackOverlay
from engine.core.logger import get_logger
from panda3d.core import WindowProperties

logger = get_logger("systems.feedback")

class FeedbackSystem(System):
    def __init__(self, world, event_bus, game):
        super().__init__(world, event_bus)
        self.game = game
        self.overlay = None
        self.overlay_visible = False
        self.reports_dir = Path("reports")
        
    def initialize(self):
        """Called when system is added to world."""
        # Create reports directory
        self.reports_dir.mkdir(exist_ok=True)
        
        # Set up keybind for F1
        self.game.accept("f1", self.toggle_overlay)
        logger.info("FeedbackSystem initialized. Press F1 to report bugs.")
        
    def toggle_overlay(self):
        if not self.overlay_visible:
            self.show_overlay()
        else:
            self.hide_overlay()
    
    def show_overlay(self):
        if not self.overlay:
            self.overlay = FeedbackOverlay(self.on_submit, self.on_cancel)
        self.overlay.show()
        self.overlay_visible = True
        
        # Unlock mouse so user can interact with UI
        # Create new properties to update
        new_props = WindowProperties()
        new_props.setCursorHidden(False)
        base.win.requestProperties(new_props)
        
    def hide_overlay(self):
        if self.overlay:
            self.overlay.hide()
        self.overlay_visible = False
        
        # Hide cursor and re-lock mouse for gameplay
        # Note: This assumes standard FPS controls where mouse is hidden/locked
        props = self.game.win.getProperties()
        props.setCursorHidden(True)
        self.game.win.requestProperties(props)
        # Re-center mouse if needed, typically handled by PlayerControlSystem
        
    def on_submit(self, data):
        logger.info(f"Submitting feedback report: {data['title']}")
        try:
            report_id = self.generate_report(data)
            logger.info(f"Report saved: {report_id}")
            self.game.messenger.send("feedback_submitted", [report_id])
        except Exception as e:
            logger.error(f"Failed to generate report: {e}", exc_info=True)
            self.game.messenger.send("feedback_failed", [str(e)])
            
        self.hide_overlay()
        
    def on_cancel(self):
        self.hide_overlay()
        
    def generate_report(self, user_data):
        # Generate unique report ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_id = uuid.uuid4().hex[:6]
        report_id = f"{timestamp}_{short_id}"
        
        # Create report package
        zip_filename = f"bug_report_{report_id}.zip"
        zip_path = self.reports_dir / zip_filename
        
        # Take screenshot if requested
        screenshot_path = None
        if user_data.get("include_screenshot", False):
            screenshot_path = self.reports_dir / f"screenshot_{report_id}.png"
            self.game.screenshot(namePrefix=str(screenshot_path.with_suffix('')), defaultExtension='png')
            # Panda3D's screenshot is async or immediate depending on backend?
            # Actually base.screenshot() saves immediately usually.
            # But the path might not be exactly as requested if it appends frame number.
            # Let's try to locate the most recent screenshot if needed, 
            # or rely on Panda3D returning the filename.
            # Actually, simplier approach: capture it right now.
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add metadata
            report_data = {
                "report_id": report_id,
                "timestamp": datetime.now().isoformat(),
                "category": user_data["category"],
                "title": user_data["title"],
                "game_version": "0.1.0-milestone1", # TODO: Get from version file
                "system": self.collect_system_info(),
                "session": self.collect_session_info(),
                "attachments": {
                    "screenshot": user_data.get("include_screenshot", False),
                    "full_logs": user_data.get("include_logs", True),
                }
            }
            zf.writestr("report.json", json.dumps(report_data, indent=2))
            
            # Add description
            zf.writestr("description.txt", user_data["description"])
            
            # Add logs
            if user_data.get("include_logs", True):
                self.add_logs_to_zip(zf)
            
            # Add screenshot if it exists
            # Note: Since screenshot might be taken slightly async or with appended numbers,
            # this part is tricky in one pass.
            # For robustness, we might skip actual inclusion inside zip for this iteration
            # if we can't guarantee file existence immediately 
            # OR we try to find it.
            # Panda saves as <namePrefix>.png or <namePrefix>.<frame>.png
            # Let's keep it simple: if we requested it, we took it, 
            # maybe we just rename it and leave it alongside the zip?
            # Or try to add it.
            if screenshot_path and screenshot_path.exists():
                 zf.write(screenshot_path, arcname="screenshot.png")
                 # Cleanup screenshot file after zipping
                 # screenshot_path.unlink() 
            
            # Alternative: if screenshot fails, we just don't include it.
            
        return report_id

    def collect_system_info(self):
        try:
            import panda3d
            return {
                "os": platform.system(),
                "os_release": platform.release(),
                "os_version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "panda3d_version": panda3d.__version__
            }
        except Exception:
            return {"error": "Could not collect system info"}

    def collect_session_info(self):
        # Placeholder for session info (FPS, position, etc)
        # In a real implementation, we'd query other systems
        return {
            "fps": round(self.game.clock.getAverageFrameRate(), 1),
            "time": self.game.taskMgr.globalClock.getFrameTime()
        }

    def add_logs_to_zip(self, zf):
        # Look for logs in logs/ directory
        log_dir = Path("logs")
        if not log_dir.exists():
            return
            
        for log_file in log_dir.glob("*.log"):
            try:
                # Read last 1000 lines to avoid massive files
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    content = "".join(lines[-1000:])
                zf.writestr(f"logs/{log_file.name}", content)
            except Exception as e:
                logger.warning(f"Failed to read log {log_file}: {e}")
                
        # Also include any CSV metrics like performance baseline
        for csv_file in log_dir.glob("*.csv"):
             try:
                # Read last 1000 lines
                with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    content = "".join(lines[-1000:])
                zf.writestr(f"logs/{csv_file.name}", content)
             except Exception:
                 pass
