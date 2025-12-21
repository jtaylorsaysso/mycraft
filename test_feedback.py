import unittest
from unittest.mock import MagicMock, patch
import json
import zipfile
import shutil
from pathlib import Path
from engine.systems.feedback import FeedbackSystem

class TestFeedbackSystem(unittest.TestCase):
    def setUp(self):
        self.mock_game = MagicMock()
        self.mock_game.clock.getAverageFrameRate.return_value = 60.0
        self.mock_game.taskMgr.globalClock.getFrameTime.return_value = 123.45
        
        # Mock window properties
        mock_props = MagicMock()
        self.mock_game.win.getProperties.return_value = mock_props
        
        self.mock_world = MagicMock()
        self.mock_event_bus = MagicMock()
        
        self.system = FeedbackSystem(self.mock_world, self.mock_event_bus, self.mock_game)
        self.system.reports_dir = Path("test_reports")
        self.system.reports_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        if self.system.reports_dir.exists():
            shutil.rmtree(self.system.reports_dir)

    def test_report_generation(self):
        # Create a dummy log file
        Path("logs").mkdir(exist_ok=True)
        with open("logs/test.log", "w") as f:
            f.write("Log line 1\nLog line 2")
            
        data = {
            "title": "Test Bug",
            "description": "This is a test description",
            "category": "bug",
            "include_screenshot": False,
            "include_logs": True
        }
        
        # Generate report
        report_id = self.system.generate_report(data)
        
        # Verify file exists
        files = list(self.system.reports_dir.glob("*.zip"))
        self.assertEqual(len(files), 1)
        zip_path = files[0]
        
        # Verify zip content
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check description
            self.assertEqual(zf.read("description.txt").decode(), "This is a test description")
            
            # Check metadata
            meta = json.loads(zf.read("report.json"))
            self.assertEqual(meta['title'], "Test Bug")
            self.assertEqual(meta['system']['python_version'][:1], "3")
            
            # Check logs
            self.assertIn("logs/test.log", zf.namelist())
            self.assertIn("Log line 1", zf.read("logs/test.log").decode())

if __name__ == '__main__':
    unittest.main()
