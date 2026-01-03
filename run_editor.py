#!/usr/bin/env python3
"""
Launch standalone MyCraft Editor Suite.

Runs the editor application without the game runtime.
This is a dev-level tool for editing models, animations, and assets.

Usage:
    python run_editor.py
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from engine.editor.app import EditorApp


def main():
    """Launch the editor suite."""
    print("🎨 Launching MyCraft Editor Suite...")
    print("   Press 1-9 to switch editors")
    print("   Press ESC to quit")
    print()
    
    app = EditorApp()
    app.run()


if __name__ == "__main__":
    main()
