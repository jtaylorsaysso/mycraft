#!/usr/bin/env python3
"""
Launch standalone MyCraft Editor Suite.

Runs the editor application without the game runtime.
This is a tool for editing models, animations, and assets.

Usage:
    python run_editor.py                    # Open with default workspace
    python run_editor.py --workspace Character  # Open Character Editor
    python run_editor.py --workspace Animation  # Open Animation Editor
    python run_editor.py --workspace Preview    # Open Preview Mode
"""

import sys
import os
import argparse

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from engine.editor.app import EditorApp


def main():
    """Launch the editor suite."""
    parser = argparse.ArgumentParser(description="MyCraft Editor Suite")
    parser.add_argument(
        "--workspace", "-w",
        choices=["Character", "Animation", "Preview"],
        help="Workspace to open on launch (default: Character)"
    )
    args = parser.parse_args()
    
    print("🎨 Launching MyCraft Editor Suite...")
    print("   Press 1-3 to switch workspaces")
    print("   Press ESC to quit")
    print()
    
    app = EditorApp(initial_workspace=args.workspace)
    app.run()


if __name__ == "__main__":
    main()
